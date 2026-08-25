package com.airesume.gateway.service;

import com.airesume.gateway.dto.AuthResponse;
import com.airesume.gateway.dto.LoginRequest;
import com.airesume.gateway.dto.RegisterRequest;
import com.airesume.gateway.model.Role;
import com.airesume.gateway.model.User;
import com.airesume.gateway.repository.UserRepository;
import com.airesume.gateway.security.JwtTokenProvider;
import lombok.RequiredArgsConstructor;
import org.springframework.security.authentication.AuthenticationManager;
import org.springframework.security.authentication.UsernamePasswordAuthenticationToken;
import org.springframework.security.crypto.password.PasswordEncoder;
import org.springframework.stereotype.Service;

@Service
@RequiredArgsConstructor
public class AuthService {

    private final UserRepository repository;
    private final PasswordEncoder passwordEncoder;
    private final JwtTokenProvider jwtTokenProvider;
    private final AuthenticationManager authenticationManager;

    public AuthResponse register(RegisterRequest request) {
        if (repository.existsByUsername(request.getUsername())) {
            throw new RuntimeException("Username already exists");
        }

        Role userRole = request.getRole() != null && request.getRole().equalsIgnoreCase("admin") 
            ? Role.ROLE_ADMIN 
            : Role.ROLE_RECRUITER;

        var user = User.builder()
                .username(request.getUsername())
                .password(passwordEncoder.encode(request.getPassword()))
                .role(userRole)
                .build();
        
        repository.save(user);
        
        var jwtToken = jwtTokenProvider.generateToken(user);
        return AuthResponse.builder()
                .token(jwtToken)
                .username(user.getUsername())
                .role(user.getRole().name())
                .build();
    }

    public AuthResponse login(LoginRequest request) {
        // Authenticate the user (throws exception if bad credentials)
        authenticationManager.authenticate(
                new UsernamePasswordAuthenticationToken(
                        request.getUsername(),
                        request.getPassword()
                )
        );
        
        var user = repository.findByUsername(request.getUsername())
                .orElseThrow();
                
        var jwtToken = jwtTokenProvider.generateToken(user);
        return AuthResponse.builder()
                .token(jwtToken)
                .username(user.getUsername())
                .role(user.getRole().name())
                .build();
    }
}
