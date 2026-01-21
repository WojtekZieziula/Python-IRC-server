# Serwer IRC

**Przedmiot:** PSI 25Z  
**Projekt:** PyIRC_Server

**Zespół:**
* Hubert Potera
* Kacper Siemionek
* Wojciech Zieziula

## Środowisko sprzętowo-programowe

* **System operacyjny:** Linux / WSL.
* **Język:** Python 3.11+.
* **Biblioteki:** Tylko standardowe (głównie `asyncio`, `logging`, `socket`) + biblioteki deweloperskie/testowe.
* **Narzędzia:**
    * `make` – zarządzanie procesem budowania/uruchamiania.
    * `docker` – środowisko prezentacyjne.
    * `telnet` – klienci do testów manualnych.


## Uruchomienie środowiska

Pobranie repozytorium
```bash
git clone https://gitlab-stud.elka.pw.edu.pl/hpotera/pyirc_server.git
cd pyirc_server
```

Instalacja zależności

```bash
make install
```

Uruchomienie aplikacji 
```bash
make run
```

Uruchomienie aplikacji w kontenerze
```bash
make docker-build
make docker-up
```

Uruchomienie testów + pokrycie kodu
```bash
make test
```

Formatowanie i lintowanie kodu
```bash
make format
make lint
```

Czyszczenie środowiska
```bash
make clean
```
