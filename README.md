# KS Milan

Nowoczesna, responsywna strona KS Milan Milanówek oparta na Django i Wagtail,
z herbem klubu w wektorowym formacie SVG.
Redaktorzy zarządzają historią, składem, aktualnościami i terminarzem z panelu
CMS pod adresem `/cms/`. Lokalnie projekt używa SQLite.

## Wymagania

- Python 3.11 lub nowszy
- Windows PowerShell (polecenia poniżej), macOS albo Linux

## Uruchomienie lokalne

```powershell
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
Copy-Item .env.example .env
python manage.py migrate
python manage.py bootstrap_site
python manage.py create_test_user
python manage.py runserver
```

Strona: <http://127.0.0.1:8000/>

Panel redakcyjny: <http://127.0.0.1:8000/cms/>

W lokalnym trybie (`DJANGO_DEBUG=True`) komenda tworzy konto administratora CMS,
jeśli jeszcze nie istnieje:

- login: `admin`
- email: `admin@example.com`
- hasło: `Admin123!`

Zmienne `TEST_CMS_USERNAME`, `TEST_CMS_EMAIL` i `TEST_CMS_PASSWORD` pozwalają
zmienić te dane. Istniejące konto nie jest nadpisywane; aby świadomie zresetować
je, uruchom `python manage.py create_test_user --update-existing`.

Jeśli PowerShell blokuje aktywację venv, uruchom polecenia przez
`.\.venv\Scripts\python.exe` zamiast aktywować środowisko.

## Zarządzanie treścią

W panelu Wagtail dodawaj zawodników i mecze w sekcji **Snippety**, a strony
historii, składu, terminarza i aktualności w eksploratorze stron. Wpisy można
zapisać jako wersje robocze i opublikować po sprawdzeniu. Zdjęcia zawodników
i artykułów dodaje się z biblioteki obrazów Wagtail.

Komenda `bootstrap_site` przygotowuje grupy Wagtail **Editors** i **Moderators**
do zarządzania zawodnikami i meczami. Konta redaktorów dodaje administrator w
panelu CMS, przypisując im odpowiednią grupę.

Terminarz w pierwszej wersji jest edytowany ręcznie. Integrację z zewnętrznym
źródłem dodamy dopiero po potwierdzeniu stabilnego i dozwolonego dostępu; ręczna
edycja pozostanie sposobem awaryjnym. Wstępny przegląd publicznych stron PZPN,
Regiowyników i Superscore nie potwierdził jeszcze udokumentowanego API/feedu,
więc aplikacja nie pobiera na razie danych z tych serwisów.

## Konfiguracja i wdrożenie

Ustawienia lokalne przechowuj w ignorowanym przez Git pliku `.env`. Przed
wdrożeniem ustaw własny, losowy `DJANGO_SECRET_KEY` (co najmniej 50 znaków),
`DJANGO_DEBUG=False` oraz `DJANGO_ALLOWED_HOSTS`. Nie używaj przykładowego
klucza w środowisku publicznym. W trybie produkcyjnym aplikacja wymusza HTTPS i
bezpieczne ciasteczka; jeśli dostawca kończy TLS na reverse proxy, skonfiguruj
zaufane przekazywanie informacji o HTTPS zgodnie z dokumentacją hostingu.

Przykładowa komenda startowa dla hostingu uruchamiającego aplikację przez
Gunicorn:

```sh
python manage.py migrate && python manage.py bootstrap_site && python manage.py create_test_user && gunicorn ksmilan.wsgi:application --bind 0.0.0.0:${PORT:-8000}
```

Migracje i `bootstrap_site` przygotowują bazę, stronę główną oraz domyślną
witrynę Wagtail. Poza debug mode tworzenie konta testowego jest pomijane.
W produkcji nie ustawiaj `CREATE_TEST_USER`; jeśli włączysz je świadomie,
ustaw również własne, silne `TEST_CMS_PASSWORD`. Hasło nie jest wtedy wypisywane
do logów. Nie używaj lokalnego hasła testowego w publicznym wdrożeniu.

Ustaw `DJANGO_SECURE_HSTS_SECONDS` dopiero po potwierdzeniu, że cała domena
działa wyłącznie przez HTTPS. HSTS nie jest włączony automatycznie, ponieważ
jego błędne ustawienie może utrudnić późniejsze odzyskanie dostępu do domeny.

SQLite nadaje się dla niewielkiej strony, jeśli hosting zapewnia trwały dysk,
kopie zapasowe i pojedynczą instancję aplikacji. Przed wyborem hostingu trzeba
sprawdzić, czy baza `db.sqlite3` i pliki mediów przetrwają wdrożenia i restarty.
Jeśli nie, wybierz zarządzaną bazę PostgreSQL i trwały magazyn plików. Nie
przechowuj zdjęć wyłącznie na efemerycznym dysku hostingu.

## Sprawdzenia

```powershell
python manage.py check
python manage.py test
```

GitHub Actions uruchamia `check` i testy przy każdym pushu oraz pull requeście.
