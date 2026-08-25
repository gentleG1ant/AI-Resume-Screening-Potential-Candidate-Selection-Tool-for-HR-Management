package com.airesume.gateway.controller;

import com.airesume.gateway.dto.AIScoringResponse;
import com.airesume.gateway.model.Candidate;
import com.airesume.gateway.model.Job;
import com.airesume.gateway.repository.CandidateRepository;
import com.airesume.gateway.repository.JobRepository;
import com.airesume.gateway.service.ResumeForwardingService;
import lombok.RequiredArgsConstructor;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;
import org.springframework.web.multipart.MultipartFile;

import java.util.List;
import java.util.stream.Collectors;

@RestController
@RequestMapping("/api/jobs")
@RequiredArgsConstructor
public class JobProcessingController {

    private final JobRepository jobRepository;
    private final CandidateRepository candidateRepository;
    private final ResumeForwardingService resumeForwardingService;

    @PostMapping("/process-resumes")
    public ResponseEntity<AIScoringResponse> processResumes(
            @RequestParam("title") String jobTitle,
            @RequestParam("description") String jobDescription,
            @RequestParam("requiredSkills") String requiredSkills,
            @RequestParam(value = "preferredSkills", required = false) String preferredSkills,
            @RequestParam(value = "minExperience", required = false) Integer minExperience,
            @RequestParam(value = "educationLevel", required = false) String educationLevel,
            @RequestParam("files") List<MultipartFile> files) {

        try {
            // 1. Save Job to Java DB
            Job job = Job.builder()
                    .title(jobTitle)
                    .description(jobDescription)
                    .build();
            jobRepository.save(job);

            // 2. Forward to Python AI microservice
            AIScoringResponse aiResponse = resumeForwardingService.forwardToAiService(
                    jobTitle, jobDescription, requiredSkills, preferredSkills, minExperience, educationLevel, files
            );

            // 3. Save Candidates locally based on AI Response
            if (aiResponse != null && aiResponse.getRankings() != null) {
                List<Candidate> candidates = aiResponse.getRankings().stream().map(rank -> 
                    Candidate.builder()
                        .name(rank.getFilename())
                        .job(job)
                        .aiScore(rank.getFinal_score())
                        .aiFeedback(rank.getRecruiter_explanation())
                        .resumeFilePath("storage/" + rank.getFilename()) // Placeholder logic
                        .build()
                ).collect(Collectors.toList());
                candidateRepository.saveAll(candidates);
            }

            return ResponseEntity.ok(aiResponse);

        } catch (Exception e) {
            e.printStackTrace();
            return ResponseEntity.internalServerError().build();
        }
    }
}
