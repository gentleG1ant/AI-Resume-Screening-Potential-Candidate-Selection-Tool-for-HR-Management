package com.airesume.gateway.dto;

import lombok.Data;
import java.util.List;

@Data
public class AIScoringResponse {
    private String status;
    private int processed_count;
    private int failed_count;
    private List<ScoredCandidateResult> rankings;

    @Data
    public static class ScoredCandidateResult {
        private String filename;
        private int rank_position;
        private double final_score;
        private Double calibrated_ml_prob;
        private double skills_required_score;
        private double skills_preferred_score;
        private double experience_score;
        private double education_score;
        private double projects_certs_score;
        private double global_context_score;
        private List<String> strengths;
        private List<String> skill_gaps;
        private List<String> top_matching_terms;
        private String recruiter_explanation;
    }
}
