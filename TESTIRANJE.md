# Testiranje aplikacije Fitness centar

## 1. Pokretanje na Linuxu

```bash
cd fitness-centar
python3 -m venv .venv
source .venv/bin/activate
python3 -m pip install -r requirements.txt
python3 main.py
```

Ako Tkinter nije instaliran:

```bash
sudo apt update
sudo apt install python3-tk
```

## 2. Test nalozi

| Uloga | Korisnicko ime | Lozinka | Namena |
|---|---|---|---|
| Administrator | admin | admin123 | Administratorske funkcije |
| Trener | trener1 | trener123 | Glavni trener sa klijentima, programima, ocenama i chatom |
| Trener | trener2 | trener123 | Drugi odobreni trener |
| Trener na cekanju | trener_pending | trener123 | Provera admin odobravanja zahteva |
| Odbijeni trener | trener_rejected | trener123 | Provera odbijenog naloga |
| Klijent | klijent1 | klijent123 | Prihvacen kod trenera1, ima program, trening, placanje, recenziju i chat |
| Klijent | klijent2 | klijent123 | Poslao zahtev treneru1 koji ceka odluku |
| Klijent | klijent3 | klijent123 | Prihvacen kod trenera1, ima dva propustena treninga i blokadu |
| Klijent | klijent4 | klijent123 | Prihvacen kod trenera2, ima kucni program i chat |

## 3. Testiranje trenera1

Prijavi se kao `trener1 / trener123`.

### Profil trenera
- Otvori svoje podatke.
- Proveri obrazovanje, licencu, biografiju, iskustvo i cenu.
- Promeni cenu jednog treninga i sacuvaj.
- Proveri da li se mesecna cena prihvacenih klijenata automatski promenila.

### Zahtevi klijenata
- Pronadji zahtev klijenta Jelena Jovanovic (`klijent2`).
- Proveri telesne podatke, cilj, lokaciju i zdravstveni problem.
- Prihvati ili odbij zahtev.

### Prihvaceni klijenti
- Petar Petrovic ima prihvacen odnos i cenu 24000.
- Luka Lukic ima dva propustena treninga.
- Proveri prikaz ciljeva, visine, tezine, lokacije i zdravstvenih problema.

### Programi i treninzi
- Petar ima program `Program snage - Petar`.
- Ima zavrsen `Trening A - noge` i dodeljen `Trening B - gornji deo`.
- Proveri vezbe unutar treninga.
- Probaj da napravis novi program/trening za Petra; treba da uspe.
- Probaj da napravis novi program/trening za Luku; aplikacija treba da zabrani dodelu jer ima dva propustena treninga.
- Probaj kopiranje Petrovog programa Luki; i to treba da bude blokirano.

### CRUD vezbi
- Postoje Cucanj, Sklek, Plank, Iskorak i Veslanje bucicama.
- Dodaj novu vezbu.
- Izmeni je.
- Obrisi je.
- Proveri unos trajanja i video URL-a.

### CRUD opreme
- Postoje sprave i rekviziti.
- Dodaj novu opremu.
- Izmeni je.
- Obrisi je.

### Ocena klijenta
- Za Petra vec postoji interna ocena 4 i komentar.
- Dodaj ili izmeni ocenu klijenta.
- Proveri da klijent tu ocenu ne vidi.

### Snimci vezbi
- Petar je poslao snimak cucnja:
  `https://example.com/uploads/petar-cucanj.mp4`
- Proveri da trener moze da vidi URL i komentar.

### Chat
- Otvori razgovor sa Petrom.
- Postoje dve test poruke.
- Posalji novu poruku.

## 4. Testiranje klijenta1

Prijavi se kao `klijent1 / klijent123`.

### Treneri
- Proveri da su trener1 i trener2 dostupni.
- Trener1 ima prosecnu ocenu 5.
- Trener na cekanju i odbijeni trener ne treba da se prikazuju kao dostupni.

### Odnos sa trenerom
- Odnos sa trenerom1 je prihvacen.
- Mesecna cena je 24000.

### Program i trening
- Otvori `Program snage - Petar`.
- Proveri zavrsen i dodeljen trening.
- Proveri video tutoriale vezbi.

### Ocena treninga i vezbe
- `Trening A - noge` vec ima ocenu 5.
- Cucanj vec ima ocenu 4.
- Probaj ocenjivanje drugog treninga ili vezbe.

### Slanje snimka
- Izaberi vezbu u treningu.
- Posalji novi test URL snimka i komentar.

### Oznacavanje treninga
- Oznaci `Trening B - gornji deo` kao zavrsen.
- Proveri promenu statusa.

### Recenzija trenera
- Trener1 vec ima recenziju ovog klijenta.
- Pokusaj da ponovo dodas recenziju; sistem treba da spreci drugu recenziju ili da dozvoli samo izmenu, zavisno od implementiranog dugmeta.

### Placanje
- Za period `2026-07` vec postoji placanje od 24000.
- Proveri istoriju placanja.
- Probaj placanje za drugi period.

### Chat
- Otvori chat sa trenerom1.
- Proveri postojece poruke i posalji novu.

## 5. Testiranje klijenta2

Prijavi se kao `klijent2 / klijent123`.

- Zahtev treneru1 je na cekanju.
- Zahtev treneru2 je odbijen.
- Posalji zahtev drugom dostupnom treneru ili ponovo treneru nakon promene statusa.
- Proveri unos visine, tezine, ciljeva, lokacije i zdravstvenih problema.

## 6. Testiranje blokade sa klijentom3

Prijavi se kao `trener1`.

- Luka Lukic ima `Kardio 1` i `Kardio 2`, oba sa statusom `missed`.
- Pokusaj da mu dodelis novi trening.
- Ocekivana poruka: klijent ima najmanje dva neodradjena treninga i nova dodela je blokirana.
- Promeni jedan propusteni trening u `completed` ili `assigned`.
- Ponovo probaj dodelu; sada treba da uspe.

## 7. Testiranje administratora

Prijavi se kao `admin / admin123`.

- Pronadji `trener_pending` i odobri zahtev.
- Proveri da nakon odobravanja moze da se prijavi i da se prikazuje klijentima.
- Proveri `trener_rejected` kao primer odbijenog zahteva.
- Proveri CRUD korisnika koji vec postoji u administratorskom delu.

## 8. Vracanje svih test podataka

Ako promenis podatke i zelis pocetno stanje:

```bash
rm -f data/fitness.db
python3 main.py
```

`main.py` ce automatski napraviti novu SQLite bazu i ubaciti sve test podatke.

## 9. Automatski testovi

```bash
PYTHONPATH=. pytest -q
```

Ocekivani rezultat:

```text
10 passed
```
