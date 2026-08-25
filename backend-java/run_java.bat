
    @echo off
    :loop
    echo Starting Maven...
    call mvn spring-boot:run
    if %errorlevel% neq 0 (
        echo Network timed out. Retrying Maven download...
        timeout /t 5
        goto loop
    )
    