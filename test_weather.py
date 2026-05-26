import requests
def execute_point(lat, lon):
    target_url = (
        f"http://api.openweathermap.org/data/2.5/forecast/daily"
        f"?lat={lat}&lon={lon}&cnt=16&units=metric"
        f"&appid=7de056ce8c3759efed8283efcad40a1d"
    )

    headers = {
        "accept": "application/json",
        "Content-Type": "application/x-www-form-urlencoded"
    }

    response = requests.get(target_url, headers=headers)

    # HTTP 상태 체크
    response.raise_for_status()

    # JSON 반환
    return response.json()


# 실행 예시
result = execute_point(37.5665, 126.9780)  # 서울 좌표

print(result)