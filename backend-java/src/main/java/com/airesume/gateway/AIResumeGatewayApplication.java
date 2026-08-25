package com.airesume.gateway;

import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;

@SpringBootApplication
public class AIResumeGatewayApplication {

    public static void main(String[] args) {
        SpringApplication.run(AIResumeGatewayApplication.class, args);
        System.out.println("🚀 AI Resume Spring Boot Gateway Started on Port 8080");
    }

}
