package com.airesume.gateway.service;

import com.airesume.gateway.dto.AIScoringResponse;
import lombok.RequiredArgsConstructor;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.core.io.ByteArrayResource;
import org.springframework.http.HttpEntity;
import org.springframework.http.HttpHeaders;
import org.springframework.http.MediaType;
import org.springframework.stereotype.Service;
import org.springframework.util.LinkedMultiValueMap;
import org.springframework.util.MultiValueMap;
import org.springframework.web.client.RestTemplate;
import org.springframework.web.multipart.MultipartFile;

import java.io.IOException;
import java.util.List;

@Service
@RequiredArgsConstructor
public class ResumeForwardingService {

    @Value("${ai-service.url:http://localhost:8000/internal/ai}")
    private String aiServiceUrl;

    public AIScoringResponse forwardToAiService(
            String jobTitle,
            String jobDescription,
            String requiredSkills,
            String preferredSkills,
            Integer minExperience,
            String educationLevel,
            List<MultipartFile> files) throws IOException {

        RestTemplate restTemplate = new RestTemplate();
        HttpHeaders headers = new HttpHeaders();
        headers.setContentType(MediaType.MULTIPART_FORM_DATA);

        MultiValueMap<String, Object> body = new LinkedMultiValueMap<>();
        body.add("job_title", jobTitle);
        body.add("job_description", jobDescription);
        body.add("required_skills", requiredSkills);
        body.add("preferred_skills", preferredSkills == null ? "" : preferredSkills);
        body.add("min_experience_years", minExperience == null ? 0 : minExperience);
        body.add("education_level", educationLevel == null ? "" : educationLevel);

        for (MultipartFile file : files) {
            ByteArrayResource fileAsResource = new ByteArrayResource(file.getBytes()) {
                @Override
                public String getFilename() {
                    return file.getOriginalFilename();
                }
            };
            body.add("files", fileAsResource);
        }

        HttpEntity<MultiValueMap<String, Object>> requestEntity = new HttpEntity<>(body, headers);

        return restTemplate.postForObject(
                aiServiceUrl + "/score-resumes",
                requestEntity,
                AIScoringResponse.class
        );
    }
}
