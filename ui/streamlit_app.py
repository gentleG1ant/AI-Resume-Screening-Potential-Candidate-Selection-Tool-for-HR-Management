import streamlit as st
import requests
import pandas as pd
import json

API_URL = "http://localhost:8000"

st.set_page_config(page_title="AI Resume Screener & Recruiter Dashboard", layout="wide")

st.title("🎯 AI/ML Resume Screening & Governance Dashboard")

# Sidebar: Job Creation & Global Controls
with st.sidebar:
    st.header("📋 1. Job Management")
    with st.expander("➕ Create New Job Posting", expanded=False):
        with st.form("create_job_form"):
            title = st.text_input("Job Title*")
            description = st.text_area("Job Description*")
            req_skills = st.text_area("Required Skills (Must have, comma separated)*")
            pref_skills = st.text_area("Preferred Skills (Nice to have, comma separated)")
            min_exp = st.number_input("Minimum Experience (Years)", min_value=0, max_value=30, value=2)
            edu_level = st.selectbox("Preferred Education", ["Any", "Bachelor", "Master", "PhD", "Diploma"])
            submit = st.form_submit_button("Publish Job")
            
            if submit:
                if title and description and req_skills:
                    res = requests.post(f"{API_URL}/jobs/", json={
                        "title": title,
                        "description": description,
                        "required_skills": req_skills
                    })
                    if res.status_code == 201:
                        st.success(f"Job created! ID: {res.json()['job_id']}")
                        st.rerun()
                    else:
                        st.error("Failed to create job")
                else:
                    st.error("Title, Description, and Required Skills are mandatory.")

# Main Panel
try:
    jobs_response = requests.get(f"{API_URL}/jobs/")
    if jobs_response.status_code == 200:
        jobs = jobs_response.json().get("jobs", [])
        if not jobs:
            st.info("No jobs found. Create one in the sidebar to get started.")
        else:
            job_options = {f"{j['title']} (ID: {j['job_id']})": j['job_id'] for j in jobs}
            selected_job_str = st.selectbox("📌 Select Active Job Posting", options=list(job_options.keys()))
            selected_job_id = job_options[selected_job_str]
            
            # Action Tabs
            tab_upload, tab_rankings, tab_compare, tab_ml_gov = st.tabs([
                "📤 Upload & Ingest", 
                "📊 Ranked Candidates", 
                "⚖️ Multi-Candidate Comparison",
                "🤖 ML Re-Ranking & Governance"
            ])
            
            # Tab 1: Upload
            with tab_upload:
                st.subheader("Bulk Resume Intake")
                st.write("Upload candidate resumes in PDF or DOCX format. The system automatically deduplicates, parses structured sections, and triggers background scoring.")
                uploaded_files = st.file_uploader("Upload PDF/DOCX Resumes", type=['pdf', 'docx'], accept_multiple_files=True)
                
                if st.button("🚀 Process & Rank Batch", type="primary"):
                    if uploaded_files:
                        with st.spinner("Streaming resumes to server & queuing pipeline..."):
                            files_payload = [("files", (f.name, f.getvalue(), f.type)) for f in uploaded_files]
                            upload_res = requests.post(f"{API_URL}/jobs/{selected_job_id}/resumes", files=files_payload)
                            if upload_res.status_code == 202:
                                st.success("Batch successfully queued! Switch to the **Ranked Candidates** tab to monitor results.")
                            else:
                                st.error(f"Upload failed: {upload_res.text}")
                    else:
                        st.warning("Please select at least one resume file.")

            # Tab 2: Ranked Candidates
            with tab_rankings:
                col_title, col_refresh = st.columns([4, 1])
                with col_title:
                    st.subheader("Candidate Leaderboard & Explainability")
                with col_refresh:
                    refresh_btn = st.button("🔄 Refresh Data")
                    
                # Filters
                f_col1, f_col2, f_col3 = st.columns(3)
                with f_col1:
                    filter_status = st.multiselect("Filter by Status", ["All", "New", "Shortlisted", "Interview", "Rejected", "Hired"], default=["All"])
                with f_col2:
                    min_score_filter = st.slider("Minimum Match Score %", min_value=0, max_value=100, value=0)
                with f_col3:
                    search_query = st.text_input("Search Candidate / Keyword")

                rankings_res = requests.get(f"{API_URL}/jobs/{selected_job_id}/rankings")
                if rankings_res.status_code == 200:
                    raw_rankings = rankings_res.json().get("rankings", [])
                    if raw_rankings:
                        df = pd.DataFrame(raw_rankings)
                        
                        # Apply filters
                        if "All" not in filter_status and filter_status:
                            df = df[df['candidate_status'].isin(filter_status)]
                        if min_score_filter > 0:
                            df = df[(df['final_rank_score'] * 100) >= min_score_filter]
                        if search_query:
                            q = search_query.lower()
                            df = df[
                                df['candidate_name'].str.lower().str.contains(q, na=False) |
                                df['top_matching_terms'].str.lower().str.contains(q, na=False) |
                                df['strengths_list'].str.lower().str.contains(q, na=False)
                            ]

                        if not df.empty:
                            # Summary Cards
                            m1, m2, m3, m4 = st.columns(4)
                            m1.metric("Total Processed", len(raw_rankings))
                            m2.metric("Filtered Candidates", len(df))
                            top_score = f"{df['final_rank_score'].max()*100:.1f}%" if not df.empty else "N/A"
                            m3.metric("Top Match Score", top_score)
                            shortlisted_count = len(df[df['candidate_status'] == 'Shortlisted'])
                            m4.metric("Shortlisted", shortlisted_count)

                            # Overview Table
                            display_df = pd.DataFrame()
                            display_df['Rank'] = df['rank_position']
                            display_df['Candidate'] = df['candidate_name']
                            display_df['Status'] = df['candidate_status']
                            display_df['Final Match'] = (df['final_rank_score'] * 100).apply(lambda x: f"{x:.1f}%")
                            display_df['Required Skills'] = (df['skills_required_score'] * 100).apply(lambda x: f"{x:.1f}%")
                            display_df['Experience Match'] = (df['experience_score'] * 100).apply(lambda x: f"{x:.1f}%")
                            display_df['Context Alignment'] = (df['global_context_score'] * 100).apply(lambda x: f"{x:.1f}%")
                            display_df['Key Strengths'] = df['strengths_list']
                            display_df['ID'] = df['candidate_id']
                            
                            st.dataframe(display_df.drop(columns=['ID']), use_container_width=True)

                            # Candidate Detail & Workflow Action section
                            st.divider()
                            st.subheader("🔍 Deep-Dive & Recruiter Decision Workflow")
                            
                            cand_list = {f"#{row['rank_position']} - {row['candidate_name']} ({row['final_rank_score']*100:.1f}%)": row['candidate_id'] for _, row in df.iterrows()}
                            selected_cand_label = st.selectbox("Select candidate to review & update status:", list(cand_list.keys()))
                            selected_cand_id = cand_list[selected_cand_label]
                            
                            cand_row = df[df['candidate_id'] == selected_cand_id].iloc[0]
                            
                            c_left, c_right = st.columns([3, 2])
                            with c_left:
                                st.markdown(f"### **{cand_row['candidate_name']}**")
                                st.markdown(f"**Source File:** `{cand_row['source_filename']}`")
                                st.info(f"💡 **AI Recruiter Summary:**\n\n{cand_row.get('explanation_string', 'No summary generated.')}")
                                
                                st.markdown("#### **Component Score Breakdown**")
                                b1, b2, b3, b4 = st.columns(4)
                                b1.progress(float(cand_row['skills_required_score']), text=f"Req. Skills: {cand_row['skills_required_score']*100:.0f}%")
                                b2.progress(float(cand_row['skills_preferred_score']), text=f"Pref. Skills: {cand_row['skills_preferred_score']*100:.0f}%")
                                b3.progress(float(cand_row['experience_score']), text=f"Experience: {cand_row['experience_score']*100:.0f}%")
                                b4.progress(float(cand_row['education_score']), text=f"Education: {cand_row['education_score']*100:.0f}%")
                                
                                st.write(f"**Verified Strengths:** {cand_row.get('strengths_list', 'N/A')}")
                                st.write(f"**Identified Skill Gaps:** {cand_row.get('skill_gaps_list', 'None identified')}")
                                st.write(f"**Shared Key Terms:** `{cand_row.get('top_matching_terms', 'N/A')}`")

                            with c_right:
                                st.markdown("#### **Update Screening Decision (Training Feedback)**")
                                with st.form(f"status_form_{selected_cand_id}"):
                                    new_status = st.selectbox(
                                        "Candidate Status", 
                                        ["New", "Shortlisted", "Interview", "Rejected", "Hired"],
                                        index=["New", "Shortlisted", "Interview", "Rejected", "Hired"].index(cand_row.get('candidate_status', 'New'))
                                    )
                                    recruiter_notes = st.text_area("Recruiter Notes / Decision Rational", value=cand_row.get('recruiter_decision', '') or '')
                                    save_status_btn = st.form_submit_button("Save Decision")
                                    
                                    if save_status_btn:
                                        patch_res = requests.patch(
                                            f"{API_URL}/candidates/{selected_cand_id}/status",
                                            json={"status": new_status, "recruiter_decision": recruiter_notes}
                                        )
                                        if patch_res.status_code == 200:
                                            st.success("Candidate status updated & recorded to ML training feedback log!")
                                            st.rerun()
                                        else:
                                            st.error("Failed to update status")
                        else:
                            st.warning("No candidates match the selected filters.")
                    else:
                        st.info("No candidates ranked for this job yet. Upload resumes to see the leaderboard.")
                else:
                    st.error("Failed to fetch rankings from API.")

            # Tab 3: Multi-Candidate Comparison
            with tab_compare:
                st.subheader("Candidate Comparison Matrix")
                if raw_rankings and len(raw_rankings) >= 2:
                    c_options = {f"{r['candidate_name']} (#{r['rank_position']})": r['candidate_id'] for r in raw_rankings}
                    selected_compare = st.multiselect("Select 2 to 4 candidates to compare:", list(c_options.keys()), default=list(c_options.keys())[:min(3, len(c_options))])
                    
                    if len(selected_compare) >= 2:
                        comp_ids = [c_options[k] for k in selected_compare]
                        comp_data = [r for r in raw_rankings if r['candidate_id'] in comp_ids]
                        
                        cols = st.columns(len(comp_data))
                        for idx, cand in enumerate(comp_data):
                            with cols[idx]:
                                st.markdown(f"### **{cand['candidate_name']}**")
                                st.markdown(f"**Overall Rank:** `#{cand['rank_position']}`")
                                st.metric("Final Score", f"{cand['final_rank_score']*100:.1f}%")
                                st.metric("Status", cand.get('candidate_status', 'New'))
                                
                                st.markdown("**Breakdowns:**")
                                st.write(f"- Required Skills: `{cand['skills_required_score']*100:.0f}%`")
                                st.write(f"- Preferred Skills: `{cand['skills_preferred_score']*100:.0f}%`")
                                st.write(f"- Experience: `{cand['experience_score']*100:.0f}%`")
                                st.write(f"- Education: `{cand['education_score']*100:.0f}%`")
                                
                                st.markdown("**Strengths:**")
                                st.caption(cand.get('strengths_list', 'N/A'))
                                
                                st.markdown("**Skill Gaps:**")
                                st.caption(cand.get('skill_gaps_list', 'None'))
                    else:
                        st.info("Please select at least 2 candidates above to view side-by-side comparison.")
                else:
                    st.info("At least two ranked candidates are needed to perform a comparison.")

            # Tab 4: ML Re-Ranking & Governance
            with tab_ml_gov:
                st.subheader("🤖 Data-Driven ML Re-Ranking & Fairness Governance")
                
                # Fetch ML status
                ml_res = requests.get(f"{API_URL}/ml/status")
                if ml_res.status_code == 200:
                    ml_data = ml_res.json()
                    
                    # Checkpoint Banner
                    real_count = ml_data.get("real_feedback_count", 0)
                    target_count = ml_data.get("checkpoint_target", 100)
                    checkpoint_reached = ml_data.get("checkpoint_reached", False)
                    
                    if checkpoint_reached:
                        st.success(f"🔔 **100-Recruitment Checkpoint Reached!** ({real_count}/{target_count} real decisions collected). You may now trigger a candidate model evaluation.")
                    else:
                        st.info(f"📊 **Recruitment Training Checkpoint Progress:** `{real_count}/{target_count}` real recruiter decisions recorded. The baseline rule-based scoring remains active.")
                    
                    st.progress(min(1.0, real_count / float(target_count)))
                    
                    # Top Metrics
                    col_m1, col_m2, col_m3 = st.columns(3)
                    col_m1.metric("Active Production Model", ml_data.get("active_model_version"))
                    col_m2.metric("Shadow Trial Model", ml_data.get("shadow_model_version"))
                    col_m3.metric("Total Training Records", ml_data.get("total_feedback_count"))
                    
                    st.divider()
                    
                    # Candidate Model Training Panel
                    st.markdown("### **1. Candidate Model Training & Calibration**")
                    train_col1, train_col2 = st.columns([2, 1])
                    with train_col1:
                        st.write("Train a calibrated Logistic Regression model on historical feedback. Evaluates Precision, Recall, F1, ROC-AUC, Brier score, and runs a statistical fairness audit.")
                        use_synth_check = st.checkbox("Cold-Start Test: Include labeled synthetic benchmark data (for development testing)", value=False)
                    with train_col2:
                        if st.button("🔬 Train & Evaluate Candidate Model", type="primary"):
                            with st.spinner("Training calibrated model & auditing statistical fairness..."):
                                train_call = requests.post(f"{API_URL}/ml/train-candidate", json={"use_synthetic": use_synth_check})
                                if train_call.status_code == 200:
                                    st.success(train_call.json().get("message"))
                                    st.rerun()
                                else:
                                    st.error(f"Training failed: {train_call.json().get('detail')}")

                    # Registered Models & Lifecycle Management
                    st.divider()
                    st.markdown("### **2. Model Registry & Human-In-The-Loop Lifecycle**")
                    registered_models = ml_data.get("registered_models", [])
                    if registered_models:
                        mod_df = pd.DataFrame(registered_models)
                        st.dataframe(mod_df, use_container_width=True)
                        
                        selected_ver = st.selectbox("Select model version for deep audit & deployment control:", [m["version"] for m in registered_models])
                        
                        # Fetch full report
                        rep_res = requests.get(f"{API_URL}/ml/reports/{selected_ver}")
                        if rep_res.status_code == 200:
                            rep_data = rep_res.json()
                            eval_rep = rep_data.get("evaluation_report", {})
                            metrics = eval_rep.get("metrics", {})
                            base_comp = eval_rep.get("baseline_comparison", {})
                            fairness_audit = rep_data.get("fairness_audit", {})
                            
                            st.markdown(f"#### **Evaluation Report: `{selected_ver}`** (Status: `{rep_data.get('lifecycle_status')}`)")
                            
                            e1, e2, e3, e4, e5 = st.columns(5)
                            e1.metric("F1-Score", metrics.get("f1_score", "N/A"), delta=f"{base_comp.get('f1_improvement', 0):+.3f} vs baseline")
                            e2.metric("Precision", metrics.get("precision", "N/A"))
                            e3.metric("Recall", metrics.get("recall", "N/A"))
                            e4.metric("ROC-AUC", metrics.get("roc_auc", "N/A"))
                            e5.metric("Brier Calibration", metrics.get("brier_score", "N/A"))
                            
                            # Fairness Audit Display
                            st.markdown("#### **Fairness & Statistical Parity Audit**")
                            if rep_data.get("fairness_alert_flag"):
                                st.warning(f"⚠️ **Fairness Review Alert:** {fairness_audit.get('recommendation')}")
                            else:
                                st.success(f"✅ {fairness_audit.get('recommendation')}")
                                
                            st.json(fairness_audit)
                            
                            # Governance Deployment Actions
                            st.markdown("#### **Authorized Deployment Action**")
                            d_col1, d_col2, d_col3, d_col4 = st.columns(4)
                            with d_col1:
                                if st.button("👥 Deploy to Shadow Mode (Trial)"):
                                    requests.post(f"{API_URL}/ml/models/{selected_ver}/lifecycle", json={"status": "SHADOW"})
                                    st.success(f"Model {selected_ver} placed into Shadow Mode!")
                                    st.rerun()
                            with d_col2:
                                if st.button("🚀 Promote to ACTIVE Production"):
                                    requests.post(f"{API_URL}/ml/models/{selected_ver}/lifecycle", json={"status": "ACTIVE"})
                                    st.success(f"Model {selected_ver} is now the ACTIVE Production Model!")
                                    st.rerun()
                            with d_col3:
                                if st.button("⏪ Rollback to RETIRED"):
                                    requests.post(f"{API_URL}/ml/models/{selected_ver}/lifecycle", json={"status": "RETIRED"})
                                    st.info(f"Model {selected_ver} retired.")
                                    st.rerun()
                            with d_col4:
                                if st.button("❌ Reject Model"):
                                    requests.post(f"{API_URL}/ml/models/{selected_ver}/lifecycle", json={"status": "REJECTED"})
                                    st.warning(f"Model {selected_ver} rejected.")
                                    st.rerun()
                    else:
                        st.info("No ML candidate models trained yet. Click 'Train & Evaluate Candidate Model' above to initiate.")
                        
                else:
                    st.error("Failed to connect to ML Governance API.")

except requests.exceptions.ConnectionError:
    st.error("⚠️ Could not connect to API server. Please make sure FastAPI is running on `http://localhost:8000`.")
