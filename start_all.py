import subprocess
import time
import os
import sys
import urllib.request
import zipfile

def check_and_download_maven():
    maven_dir = os.path.join(os.getcwd(), "maven")
    if not os.path.exists(maven_dir):
        print("Downloading Apache Maven for Java compilation...")
        url = "https://archive.apache.org/dist/maven/maven-3/3.9.6/binaries/apache-maven-3.9.6-bin.zip"
        urllib.request.urlretrieve(url, "maven.zip")
        with zipfile.ZipFile("maven.zip", 'r') as zip_ref:
            zip_ref.extractall(".")
        os.rename("apache-maven-3.9.6", "maven")
        print("Maven downloaded successfully.")

def start_python_ai():
    print("Starting Python AI Engine (Port 8000)...")
    python_exe = os.path.join("venv", "Scripts", "python.exe") if os.path.exists("venv") else "python"
    return subprocess.Popen(
        [python_exe, "-m", "uvicorn", "api.main:app", "--port", "8000"],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.STDOUT
    )

def start_java_gateway():
    print("Starting Java API Gateway (Port 8080)...")
    print("Note: Java will automatically download Spring Boot libraries. This may take 1-2 minutes...")
    
    java_home = os.path.join(os.getcwd(), "jdk-21")
    # Use 8.3 short path if possible to avoid parenthesis issues in paths
    if sys.platform == "win32":
        import ctypes
        buf = ctypes.create_unicode_buffer(256)
        ctypes.windll.kernel32.GetShortPathNameW(java_home, buf, 256)
        java_home = buf.value

    env = os.environ.copy()
    env["JAVA_HOME"] = java_home
    current_path = env.get("PATH", env.get("Path", ""))
    env["PATH"] = os.path.join(os.getcwd(), "maven", "bin") + os.pathsep + os.path.join(java_home, "bin") + os.pathsep + current_path

    # Run Maven in a loop to bypass network timeouts
    mvn_cmd = "mvn spring-boot:run"
    batch_script = f"""
    @echo off
    :loop
    echo Starting Maven...
    call {mvn_cmd}
    if %errorlevel% neq 0 (
        echo Network timed out. Retrying Maven download...
        timeout /t 5
        goto loop
    )
    """
    with open(os.path.join("backend-java", "run_java.bat"), "w") as f:
        f.write(batch_script)

    return subprocess.Popen(
        ["cmd.exe", "/c", "run_java.bat"],
        cwd=os.path.join(os.getcwd(), "backend-java"),
        env=env
    )

def start_react_ui():
    print("Starting React UI (Port 5173)...")
    env = os.environ.copy()
    current_path = env.get("PATH", env.get("Path", ""))
    env["PATH"] = os.path.join(os.getcwd(), "node") + os.pathsep + current_path
    
    # Ensure node_modules exists
    if not os.path.exists(os.path.join("frontend-react", "node_modules")):
        print("Installing React dependencies (this happens once)...")
        subprocess.run(["npm", "install"], cwd="frontend-react", env=env, shell=True)

    return subprocess.Popen(
        ["npm", "run", "dev"],
        cwd=os.path.join(os.getcwd(), "frontend-react"),
        env=env,
        shell=True
    )

if __name__ == "__main__":
    print("=====================================================")
    print("   AI Resume Screening System - Enterprise Edition")
    print("=====================================================\n")
    
    check_and_download_maven()
    
    p1 = start_python_ai()
    p2 = start_java_gateway()
    p3 = start_react_ui()
    
    print("\nAll servers have been triggered!")
    print("UI will be available at: http://localhost:5173")
    print("Note: Wait about 60 seconds before logging in so Java can finish booting.")
    print("\nPress Ctrl+C to stop all servers.")
    
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nStopping servers...")
        p1.terminate()
        p2.terminate()
        p3.terminate()
        print("Servers stopped.")
