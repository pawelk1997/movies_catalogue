import tmdb_client
import requests
import pytest
from unittest.mock import Mock
from main import app

# Sample data for mocking API responses
mock_movie_details = {
    "title": "The Matrix",
    "id": 603,
    "overview": "A computer hacker learns from mysterious rebels about the true nature of his reality...",
    "release_date": "1999-03-30"
}

mock_cast_data = {
    "cast": [
        {"name": "Keanu Reeves", "character": "Neo"},
        {"name": "Laurence Fishburne", "character": "Morpheus"},
        {"name": "Carrie-Anne Moss", "character": "Trinity"},
    ]
}

mock_images_data = {
    "backdrops": [{"file_path": "/path/to/backdrop1.jpg"}, {"file_path": "/path/to/backdrop2.jpg"}],
    "posters": [{"file_path": "/path/to/poster1.jpg"}, {"file_path": "/path/to/poster2.jpg"}],
}


def test_get_single_movie_success(monkeypatch):
    """
    Testuje funkcję get_single_movie w przypadku udanej odpowiedzi API.
    Sprawdza, czy funkcja wywołuje poprawny endpoint i zwraca oczekiwane dane.
    """
    mock_response = Mock()
    mock_response.json.return_value = mock_movie_details
    mock_response.raise_for_status = Mock()

    # Zamiana requests.get na nasz obiekt Mock
    monkeypatch.setattr(requests, "get", Mock(return_value=mock_response))

    movie_id = 603
    movie_details = tmdb_client.get_single_movie(movie_id)

    # Sprawdzenie, czy requests.get został wywołany z poprawnym adresem URL
    requests.get.assert_called_with(
        f"https://api.themoviedb.org/3/movie/{movie_id}",
        headers={"Authorization": f"Bearer {tmdb_client.API_TOKEN}"}
    )
    # Sprawdzenie, czy zwrócone dane są zgodne z naszym mockiem
    assert movie_details == mock_movie_details


def test_get_single_movie_http_error(monkeypatch):
    """
    Testuje get_single_movie w przypadku błędu HTTP.
    Oczekuje, że zostanie zgłoszony błąd HTTPError.
    """
    mock_response = Mock()
    mock_response.raise_for_status.side_effect = requests.exceptions.HTTPError("Not Found")
    
    # Zamiana requests.get na nasz obiekt Mock, który zgłasza błąd
    monkeypatch.setattr(requests, "get", Mock(return_value=mock_response))

    with pytest.raises(requests.exceptions.HTTPError):
        tmdb_client.get_single_movie(999999) # Używamy nieistniejącego ID
        
        
def test_get_single_movie_cast_success(monkeypatch):
    """
    Testuje funkcję get_single_movie_cast.
    Sprawdza, czy endpoint jest poprawny i zwraca tylko listę obsady.
    """
    mock_response = Mock()
    mock_response.json.return_value = mock_cast_data
    mock_response.raise_for_status = Mock()

    monkeypatch.setattr(requests, "get", Mock(return_value=mock_response))

    movie_id = 603
    movie_cast = tmdb_client.get_single_movie_cast(movie_id)

    # Sprawdzenie, czy wywołano poprawny URL dla obsady
    requests.get.assert_called_with(
        f"https://api.themoviedb.org/3/movie/{movie_id}/credits",
        headers={"Authorization": f"Bearer {tmdb_client.API_TOKEN}"}
    )
    # Sprawdzenie, czy zwrócona została poprawna lista z klucza 'cast'
    assert movie_cast == mock_cast_data["cast"]


def test_get_movie_images_success(monkeypatch):
    """
    Testuje funkcję get_movie_images.
    Sprawdza poprawność endpointa i zwracanych danych.
    """
    mock_response = Mock()
    mock_response.json.return_value = mock_images_data
    mock_response.raise_for_status = Mock()

    monkeypatch.setattr(requests, "get", Mock(return_value=mock_response))

    movie_id = 603
    movie_images = tmdb_client.get_movie_images(movie_id)

    # Sprawdzenie, czy wywołano poprawny URL dla obrazów
    requests.get.assert_called_with(
        f"https://api.themoviedb.org/3/movie/{movie_id}/images",
        headers={"Authorization": f"Bearer {tmdb_client.API_TOKEN}"}
    )
    # Sprawdzenie, czy zwrócono kompletny słownik z obrazami
    assert movie_images == mock_images_data


@pytest.mark.parametrize("list_type", ['popular', 'top_rated', 'now_playing', 'upcoming'])
def test_homepage(monkeypatch, list_type):
    """
    Testuje stronę główną dla różnych typów list filmów.
    Sprawdza, czy aplikacja zwraca kod 200 i wywołuje odpowiednią funkcję
    do pobierania listy filmów.
    """
    api_mock = Mock(return_value={'results':[mock_movie_details]*8})
    monkeypatch.setattr("tmdb_client.get_movies_list", api_mock)

    with app.test_client() as client:
        response = client.get(f'/?list_type={list_type}')
        assert response.status_code == 200

        api_mock.assert_called_once_with(list_type)