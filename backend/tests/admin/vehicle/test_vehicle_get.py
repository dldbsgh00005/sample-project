import pytest
from sqlmodel import Session, delete
from app.db.models.vehicle import Vehicle
from sqlalchemy import text
  
from tests.helpers import master_token, semi_admin_token, user_token, create_dummy_vehicles, create_test_rent

def test_get_vehicle_list_success(client, session, create_dummy_vehicles, master_token):
    """ 차량 목록 조회 성공 테스트"""
    vehicles = create_dummy_vehicles(3)
    
    # WHEN: /admin/vehicles 엔드포인트를 GET 요청
    response = client.get(
        "/api/admin/vehicles?page=1&pageSize=10",
        headers={"Authorization": f"Bearer {master_token}"}
    )
    
    # THEN: 응답이 성공적이고, 각 차량 필드가 올바르게 매핑됨
    assert response.status_code == 200
    data = response.json()
    assert data["resultCode"] == "SUCCESS"
    assert "vehicles" in data["data"]
    vehicles = data["data"]["vehicles"]
    assert isinstance(vehicles, list)
    assert len(vehicles) >= 3
    
    # 첫 번째 차량 데이터 검증
    vehicle = vehicles[0]
    assert "vehicle_id" in vehicle
    assert "vin" in vehicle
    assert "vehicle_number" in vehicle
    assert isinstance(vehicle["current_location"], dict)
    assert "x" in vehicle["current_location"]
    assert "y" in vehicle["current_location"]

def test_get_vehicle_list_unauthorized(client):
    """ 인증 토큰 없이 호출 시 401 Unauthorized 반환 확인"""
    response = client.get("/api/admin/vehicles?page=1&pageSize=10")
    assert response.status_code == 401

def test_get_vehicle_list_non_admin(client, session, create_dummy_vehicles, user_token):
    """ 비관리자 토큰으로 호출 시 403 Forbidden 반환 확인"""
    create_dummy_vehicles(3)

    # WHEN: /admin/vehicles 엔드포인트를 비관리자 토큰으로 호출
    response = client.get(
        "/api/admin/vehicles?page=1&pageSize=10",
        headers={"Authorization": f"Bearer {user_token}"}
    )
    # THEN: 403 Forbidden 응답이 발생함
    assert response.status_code == 403

def test_get_vehicle_list_empty(client, session, master_token):
    """ 차량 테이블을 초기화하여 빈 상태로 만듦"""
    session.exec(text("DELETE FROM vehicle"))
    session.commit()

    # WHEN: 관리자 토큰으로 빈 차량 목록 조회 요청
    response = client.get(
        "/api/admin/vehicles?page=1&pageSize=10",
        headers={"Authorization": f"Bearer {master_token}"}
    )
    # THEN: 응답 결과는 빈 리스트이어야 함
    assert response.status_code == 200
    data = response.json()
    assert data["resultCode"] == "SUCCESS"
    vehicles = data["data"]["vehicles"]
    assert isinstance(vehicles, list)
    assert len(vehicles) == 0

def test_get_vehicle_list_pagination(client, session, create_dummy_vehicles, master_token):
    """ 페이지네이션 테스트"""
    # 기존 차량 데이터 삭제
    session.exec(delete(Vehicle))
    session.commit()
    create_dummy_vehicles(5)

    # WHEN: 페이지 사이즈 3으로 각 페이지 요청 (page1, page2, page3)
    response1 = client.get(
        "/api/admin/vehicles?page=1&pageSize=3",
        headers={"Authorization": f"Bearer {master_token}"}
    )
    response2 = client.get(
        "/api/admin/vehicles?page=2&pageSize=3",
        headers={"Authorization": f"Bearer {master_token}"}
    )
    response3 = client.get(
        "/api/admin/vehicles?page=3&pageSize=3",
        headers={"Authorization": f"Bearer {master_token}"}
    )

    # THEN: page1은 3개, page2는 2개, page3는 빈 리스트
    data1 = response1.json()
    data2 = response2.json()
    data3 = response3.json()
    assert len(data1["data"]["vehicles"]) == 3
    assert len(data2["data"]["vehicles"]) == 2
    assert len(data3["data"]["vehicles"]) == 0

def test_get_vehicle_list_invalid_page(client, master_token):
    """ 유효하지 않은 페이지 값으로 호출 시 422 에러 반환 확인"""
    # WHEN: page 값이 0으로 GET 요청 시
    response = client.get(
        "/api/admin/vehicles?page=0&pageSize=10",
        headers={"Authorization": f"Bearer {master_token}"}
    )
    # THEN: 유효성 검사 실패로 422 에러가 발생함
    assert response.status_code == 422

def test_get_vehicle_list_invalid_page_size(client, master_token):
    """ 유효하지 않은 페이지 크기 값으로 호출 시 422 에러 반환 확인"""
    # WHEN: pageSize 값이 0으로 GET 요청 시
    response = client.get(
        "/api/admin/vehicles?page=1&pageSize=0",
        headers={"Authorization": f"Bearer {master_token}"}
    )
    # THEN: 유효성 검사 실패로 422 에러가 발생함
    assert response.status_code == 422
