"""
Auto-start script cho mini-adaptive-learning project
Chạy tất cả services trong các terminal riêng biệt

Usage: python app.py
"""

import subprocess
import os
import sys
import time
import platform
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Màu sắc cho terminal
class Colors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'

def print_step(message):
    """In ra bước thực hiện với màu sắc"""
    print(f"{Colors.OKCYAN}{Colors.BOLD}>>> {message}{Colors.ENDC}")

def print_success(message):
    """In ra thông báo thành công"""
    print(f"{Colors.OKGREEN}✓ {message}{Colors.ENDC}")

def print_error(message):
    """In ra thông báo lỗi"""
    print(f"{Colors.FAIL}✗ {message}{Colors.ENDC}")

def print_warning(message):
    """In ra thông báo cảnh báo"""
    print(f"{Colors.WARNING}⚠ {message}{Colors.ENDC}")

# Lấy đường dẫn project root
PROJECT_ROOT = Path(__file__).parent.absolute()
os.chdir(PROJECT_ROOT)

def check_docker_running():
    """Kiểm tra Docker Desktop có đang chạy không"""
    try:
        result = subprocess.run(
            ["docker", "info"],
            capture_output=True,
            text=True,
            timeout=5
        )
        return result.returncode == 0
    except Exception:
        return False

def start_docker_desktop():
    """Khởi động Docker Desktop"""
    print_step("Kiểm tra Docker Desktop...")
    
    if check_docker_running():
        print_success("Docker Desktop đang chạy")
        return True
    
    print_warning("Docker Desktop chưa chạy. Đang khởi động...")
    
    system = platform.system()
    
    try:
        if system == "Windows":
            # Thử khởi động Docker Desktop trên Windows
            subprocess.Popen([
                "C:\\Program Files\\Docker\\Docker\\Docker Desktop.exe"
            ])
        elif system == "Darwin":  # macOS
            subprocess.Popen(["open", "-a", "Docker"])
        else:  # Linux
            subprocess.Popen(["systemctl", "--user", "start", "docker-desktop"])
        
        # Đợi Docker khởi động (tối đa 60 giây)
        print("Đang đợi Docker Desktop khởi động...")
        for i in range(60):
            time.sleep(2)
            if check_docker_running():
                print_success("Docker Desktop đã khởi động thành công")
                return True
            if i % 5 == 0:
                print(f"  Đợi... ({i*2}s)")
        
        print_error("Docker Desktop không khởi động được sau 60 giây")
        print_warning("Vui lòng khởi động Docker Desktop thủ công và chạy lại script")
        return False
        
    except Exception as e:
        print_error(f"Lỗi khi khởi động Docker Desktop: {e}")
        print_warning("Vui lòng khởi động Docker Desktop thủ công và chạy lại script")
        return False

def find_venv_activate():
    """Tìm file activate của venv"""
    venv_paths = [
        PROJECT_ROOT / "venv" / "Scripts" / "activate.ps1",  # Windows PowerShell
        PROJECT_ROOT / "venv" / "Scripts" / "activate.bat",  # Windows CMD
        PROJECT_ROOT / ".venv" / "Scripts" / "activate.ps1",
        PROJECT_ROOT / ".venv" / "Scripts" / "activate.bat",
        PROJECT_ROOT / "venv" / "bin" / "activate",  # Unix
        PROJECT_ROOT / ".venv" / "bin" / "activate",
    ]
    
    for path in venv_paths:
        if path.exists():
            return path
    return None

def get_python_executable():
    """Lấy đường dẫn Python executable (ưu tiên venv)"""
    venv_pythons = [
        PROJECT_ROOT / "venv" / "Scripts" / "python.exe",
        PROJECT_ROOT / ".venv" / "Scripts" / "python.exe",
        PROJECT_ROOT / "venv" / "bin" / "python",
        PROJECT_ROOT / ".venv" / "bin" / "python",
    ]
    
    for python_path in venv_pythons:
        if python_path.exists():
            print_success(f"Sử dụng Python từ venv: {python_path}")
            return str(python_path)
    
    print_warning("Không tìm thấy venv, sử dụng Python hệ thống")
    return sys.executable

def start_service_in_terminal(title, command, wait_before=0):
    """
    Khởi động một service trong terminal riêng
    
    Args:
        title: Tên hiển thị của terminal
        command: Lệnh cần chạy
        wait_before: Thời gian đợi trước khi chạy lệnh (giây)
    """
    system = platform.system()
    
    if wait_before > 0:
        time.sleep(wait_before)
    
    print_step(f"Khởi động {title}...")
    
    try:
        if system == "Windows":
            # Tạo script file tạm thời để tránh vấn đề escaping
            import tempfile
            
            # Tìm venv activate script
            venv_activate = find_venv_activate()
            activate_lines = []
            
            if venv_activate and venv_activate.suffix == ".ps1":
                activate_lines = [
                    f"Write-Host 'Activating virtual environment...' -ForegroundColor Yellow",
                    f". '{venv_activate}'",
                    f"if ($LASTEXITCODE -eq 0 -or $?) {{",
                    f"    Write-Host '✓ Virtual environment activated' -ForegroundColor Green",
                    f"}} else {{",
                    f"    Write-Host '✗ Failed to activate venv' -ForegroundColor Red",
                    f"}}",
                    f"Write-Host ''"
                ]
            
            activate_block = '\n'.join(activate_lines) if activate_lines else "Write-Host 'No venv found, using system Python' -ForegroundColor Yellow"
            
            # PowerShell script content
            ps_script = f"""# {title}
$Host.UI.RawUI.WindowTitle = '{title}'
Set-Location '{PROJECT_ROOT}'
Write-Host '>>> {title}' -ForegroundColor Cyan
Write-Host 'Directory: {PROJECT_ROOT}' -ForegroundColor Gray
Write-Host ''

# Activate venv TRƯỚC KHI chạy command
{activate_block}

# Run command
Write-Host 'Starting service...' -ForegroundColor Cyan
{command}
"""
            
            # Tạo temp file
            fd, script_path = tempfile.mkstemp(suffix='.ps1', text=True)
            try:
                with os.fdopen(fd, 'w', encoding='utf-8') as f:
                    f.write(ps_script)
                
                # Start PowerShell với script file
                subprocess.Popen(
                    [
                        'powershell.exe',
                        '-NoExit',
                        '-ExecutionPolicy', 'Bypass',
                        '-File', script_path
                    ],
                    creationflags=subprocess.CREATE_NEW_CONSOLE,
                    cwd=str(PROJECT_ROOT)
                )
                
                print_success(f"{title} đã được khởi động")
                # Không xóa file ngay, để terminal có thể đọc
                # File sẽ tự động bị xóa khi hệ thống restart
                return True
                
            except Exception as e:
                # Cleanup nếu có lỗi
                try:
                    os.unlink(script_path)
                except:
                    pass
                raise e
            
        elif system == "Darwin":  # macOS
            apple_script = f'''
            tell application "Terminal"
                do script "cd '{PROJECT_ROOT}' && echo '>>> {title}' && {command}"
                activate
            end tell
            '''
            subprocess.Popen(["osascript", "-e", apple_script])
            print_success(f"{title} đã được khởi động")
            return True
            
        else:  # Linux
            # Thử các terminal emulator phổ biến
            terminals = ["gnome-terminal", "xterm", "konsole"]
            for term in terminals:
                try:
                    subprocess.Popen([
                        term, "--", "bash", "-c",
                        f"cd '{PROJECT_ROOT}' && echo '>>> {title}' && {command}; exec bash"
                    ])
                    print_success(f"{title} đã được khởi động")
                    return True
                except FileNotFoundError:
                    continue
            
            print_error("Không tìm thấy terminal emulator nào")
            return False
        
    except Exception as e:
        print_error(f"Lỗi khi khởi động {title}: {e}")
        print_warning("Thử phương pháp dự phòng...")
        
        # Fallback method for Windows - CMD
        if system == "Windows":
            try:
                # Tạo batch file cho CMD
                import tempfile
                
                bat_content = f"""@echo off
title {title}
cd /d "{PROJECT_ROOT}"
echo ^>^>^> {title}
echo Directory: {PROJECT_ROOT}
echo.
{command}
"""
                
                fd, bat_path = tempfile.mkstemp(suffix='.bat', text=True)
                try:
                    with os.fdopen(fd, 'w') as f:
                        f.write(bat_content)
                    
                    subprocess.Popen(
                        ['cmd.exe', '/K', bat_path],
                        creationflags=subprocess.CREATE_NEW_CONSOLE,
                        cwd=str(PROJECT_ROOT)
                    )
                    
                    print_success(f"{title} đã được khởi động (CMD)")
                    return True
                    
                except Exception as e2:
                    try:
                        os.unlink(bat_path)
                    except:
                        pass
                    raise e2
                    
            except Exception as e3:
                print_error(f"Phương pháp dự phòng cũng thất bại: {e3}")
                return False
        
        return False

def main():
    """Hàm chính"""
    print(f"{Colors.HEADER}{Colors.BOLD}")
    print("=" * 70)
    print("  MINI ADAPTIVE LEARNING - AUTO START SCRIPT")
    print("=" * 70)
    print(f"{Colors.ENDC}\n")
    
    # Bước 1: Khởi động Docker Desktop
    if not start_docker_desktop():
        print_error("Không thể tiếp tục mà không có Docker")
        return
    
    # Đợi một chút để Docker ổn định
    time.sleep(3)
    
    # Bước 2: Chạy docker-compose
    print_step("Khởi động Docker services (docker-compose up -d)...")
    result = subprocess.run(
        ["docker-compose", "up", "-d"],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True
    )
    
    if result.returncode == 0:
        print_success("Docker services đã khởi động")
    else:
        print_error("Lỗi khi khởi động docker-compose:")
        print(result.stderr)
        print_warning("Tiếp tục khởi động các service khác...")
    
    # Đợi Docker services khởi động hoàn toàn
    print("Đợi Docker services khởi động hoàn toàn...")
    time.sleep(5)
    
    # Bước 3: Khởi động Backend Quiz API
    # Sử dụng python từ venv (sẽ được activate trong terminal mới)
    quiz_api_cmd = 'python -m uvicorn backend.quiz_api.main:app --host 0.0.0.0 --port 8001 --reload'
    start_service_in_terminal("Backend Quiz API (Port 8001)", quiz_api_cmd, wait_before=2)
    
    # Bước 4: Khởi động Backend SAINT Analysis API
    saint_api_cmd = 'python -m uvicorn backend.saint_analysis.main:app --host 0.0.0.0 --port 8000 --reload'
    start_service_in_terminal("Backend SAINT Analysis API (Port 8000)", saint_api_cmd, wait_before=2)
    
    # Bước 5: Khởi động Frontend
    frontend_path = PROJECT_ROOT / "frontend" / "quiz-app"
    if frontend_path.exists():
        frontend_cmd = f"cd '{frontend_path}'; npm start"
        start_service_in_terminal("Frontend Quiz App", frontend_cmd, wait_before=2)
    else:
        print_warning(f"Không tìm thấy frontend tại {frontend_path}")
    
    # Thông báo hoàn tất
    print(f"\n{Colors.OKGREEN}{Colors.BOLD}")
    print("=" * 70)
    print("  ✓ TẤT CẢ SERVICES ĐÃ ĐƯỢC KHỞI ĐỘNG!")
    print("=" * 70)
    print(f"{Colors.ENDC}\n")
    
    print("Các services đang chạy:")
    print(f"  • Docker Services (Milvus, MongoDB)")
    print(f"  • Backend Quiz API: http://localhost:8001")
    print(f"  • Backend SAINT Analysis API: http://localhost:8000")
    print(f"  • Frontend Quiz App: http://localhost:3000")
    print(f"\n{Colors.WARNING}Lưu ý: Đóng các cửa sổ terminal để dừng services{Colors.ENDC}\n")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print(f"\n{Colors.WARNING}Script đã bị hủy bởi người dùng{Colors.ENDC}")
    except Exception as e:
        print_error(f"Lỗi không mong muốn: {e}")
        import traceback
        traceback.print_exc()
