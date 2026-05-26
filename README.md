# ML-WHEELS

ML-WHEELS to prosta gra wyścigowa 2D w Pythonie, napisana z użyciem
Pygame. Projekt zawiera lokalny tryb gry dla dwóch osób, edytor torów oraz
trening kierowcy AI metodą NEAT, czyli ewolucją struktur sieci neuronowych.

## Uruchomienie

Wymagania projektu są zapisane w `requirements.txt`:

```bash
pip install -r requirements.txt
python main.py
```

Główne okno startuje z menu, w którym można wybrać tryb gry, trening AI,
oglądanie zapisanego zwycięzcy albo edycję toru.

## Struktura projektu

- `main.py` - punkt wejścia aplikacji.
- `game/app.py` - główna pętla menu i przełączanie trybów.
- `game/models/car.py` - model fizyki samochodu.
- `game/models/track.py` - model toru, checkpointy, meta, zapis i odczyt toru.
- `game/logic/race.py` - logika okrążeń, kolizji i checkpointów.
- `game/logic/sensors.py` - czujniki samochodu używane przez AI.
- `game/ai/training.py` - trening NEAT i odtwarzanie najlepszego genomu.
- `game/modes/human.py` - lokalna gra dla dwóch graczy.
- `game/modes/track_editor.py` - edytor własnych torów.
- `neat_config.txt` - konfiguracja algorytmu NEAT.
- `track_layout.json` - aktualnie zapisany tor.
- `winner.pkl` - zapisany najlepszy genom po treningu.

## Logika gry

Gra działa na torze wygenerowanym z linii środkowej. Tor jest kompilowany do
powierzchni Pygame oraz maski kolizji. Maska określa, które piksele należą do
drogi. Jeśli narożnik samochodu wyjedzie poza maskę albo poza ekran, samochód
uderza w ścianę.

Każdy samochód ma osobny `RaceState`, który przechowuje:

- liczbę okrążeń,
- aktualny checkpoint,
- informację, czy meta jest już aktywna,
- informację, czy samochód znajduje się na mecie,
- informację o kraksie.

Okrążenie można zaliczyć dopiero po przejechaniu wszystkich checkpointów w
kolejności. Po ostatnim checkpoincie meta zostaje uzbrojona. Dopiero wtedy
wjazd na linię mety zwiększa licznik okrążeń i resetuje checkpointy do
kolejnego okrążenia.

W trybie lokalnym wykrywane są też zderzenia między dwoma samochodami.
Kolizja samochodów kończy przejazd obu graczy do czasu restartu.

## Samochody

Wszystkie samochody używają tej samej klasy `Car`. Auto nie porusza się po
sztywnej siatce, tylko ma prostą fizykę opartą o prędkość, kierunek jazdy i
boczny poślizg.

Najważniejsze parametry samochodu:

- rozmiar: `22 x 38` pikseli,
- maksymalna prędkość do przodu: `6.5`,
- maksymalna prędkość do tyłu: połowa prędkości maksymalnej,
- przyspieszenie: `0.18`,
- hamowanie: `0.14`,
- tarcie toczenia: `0.025`,
- opór ruchu: `0.992`,
- prędkość skrętu: `3.2`,
- przyczepność opon: `0.22`,
- maksymalna korekta boczna: `0.28`.

Sterowanie zmienia prędkość wzdłuż osi samochodu. Skręt działa tylko wtedy,
gdy samochód faktycznie się porusza, a jego siła zależy od prędkości. Model
liczy też prędkość boczną i stopniowo ją koryguje, dzięki czemu auto może
mieć lekki poślizg zamiast natychmiastowego obrotu bez bezwładności.

Kolizje ze ścianą są sprawdzane przez narożniki samochodu. Narożniki są
obracane zgodnie z aktualnym kątem auta, więc kolizja odpowiada faktycznemu
położeniu prostokąta samochodu.

## AI

AI steruje takim samym samochodem jak gracz. Różnica polega tylko na tym, że
wejścia sterowania są wybierane przez sieć neuronową NEAT.

### Wejścia sieci

Sieć ma `8` wejść:

- `5` odczytów czujników odległości od ściany,
- aktualna prędkość samochodu podzielona przez prędkość maksymalną,
- kierunek do następnego celu,
- odległość do następnego celu.

Czujniki są promieniami wysyłanymi pod kątami:

```text
-80, -40, 0, 40, 80 stopni względem kierunku samochodu
```

Każdy czujnik ma maksymalny zasięg `220` pikseli i idzie co `4` piksele aż do
ściany, granicy ekranu albo limitu zasięgu. Wynik jest normalizowany do
zakresu `0.0 - 1.0`.

Kierunek do celu to różnica między kątem auta a kątem do kolejnego checkpointu
albo mety. Wartość jest dzielona przez `180`, więc mieści się mniej więcej w
zakresie `-1.0 - 1.0`. Odległość do celu jest dzielona przez przekątną ekranu.

### Wyjścia sieci

Sieć ma `4` wyjścia:

- gaz,
- hamulec / cofanie,
- skręt w lewo,
- skręt w prawo.

Każde wyjście jest traktowane jako aktywne, jeśli ma wartość większą niż
`0.5`. Aktywne wyjścia są przekazywane bezpośrednio do `car.move(...)`.

### Trening NEAT

Trening korzysta z biblioteki `neat-python` i konfiguracji z
`neat_config.txt`.

Domyślne ustawienia z menu:

- liczba generacji: `50`,
- maksymalna liczba kroków na generację: `1800`,
- cel treningu: `3` okrążenia.

Zakresy ustawień w menu:

- generacje: `1 - 500`, krok `5`,
- maksymalne kroki: `300 - 5000`, krok `100`,
- docelowe okrążenia: `1 - 10`, krok `1`.

W każdej generacji tworzona jest populacja samochodów. Każdy genom dostaje
własną sieć, samochód i stan wyścigu. Samochody jadą równolegle, dopóki nie
rozbiją się, nie osiągną celu albo nie skończy się limit kroków.

Najlepszy genom po treningu jest zapisywany do `winner.pkl`. Tryb `Watch AI`
wczytuje ten plik i uruchamia zapisane AI na aktualnym torze.

### Wagi nagrody

Funkcja fitness jest naliczana w `game/ai/training.py`.

Nagrody i kary:

- jazda do przodu: `max(car.speed, 0) * 0.02` za krok,
- uderzenie w ścianę: `-2.0` i usunięcie samochodu z generacji,
- zaliczony checkpoint: `+20.0`,
- ukończone okrążenie: `+100.0`,
- zbyt niska prędkość, poniżej `0.15`: `-0.03` za krok,
- osiągnięcie docelowej liczby okrążeń: `+250.0` i koniec przejazdu.

Taka funkcja nagrody zachęca AI do jazdy do przodu, przejeżdżania przez
checkpointy w poprawnej kolejności i kończenia okrążeń. Kara za wolną jazdę
ogranicza strategie polegające na staniu w miejscu, a kara za kolizję usuwa
genomy, które nie potrafią utrzymać się na torze.

### Konfiguracja sieci

Najważniejsze ustawienia z `neat_config.txt`:

- populacja: `30`,
- kryterium fitness: `max`,
- próg fitness: `500.0`,
- aktywacja neuronów: `tanh`,
- sieć: jednokierunkowa (`feed_forward = True`),
- początkowe połączenia: pełne (`initial_connection = full`),
- liczba wejść: `8`,
- liczba wyjść: `4`,
- początkowa liczba neuronów ukrytych: `0`,
- mutacja wag: `weight_mutate_rate = 0.8`,
- siła mutacji wag: `weight_mutate_power = 0.5`,
- zastępowanie wag: `weight_replace_rate = 0.1`,
- zakres wag: od `-30` do `30`,
- dodanie połączenia: `conn_add_prob = 0.5`,
- usunięcie połączenia: `conn_delete_prob = 0.3`,
- dodanie neuronu: `node_add_prob = 0.2`,
- usunięcie neuronu: `node_delete_prob = 0.2`,
- elitaryzm reprodukcji: `2`,
- próg przetrwania: `0.2`.

## Tryby

### Play

Lokalny wyścig dla dwóch graczy.

Sterowanie:

- gracz niebieski: `W`, `A`, `S`, `D`,
- gracz złoty: strzałki.

`Esc` wraca do menu. Po kraksie można zrestartować wyścig klawiszem `R`.

### Train AI

Uruchamia trening NEAT. Parametry treningu wybiera się w menu przed startem:
liczbę generacji, maksymalną liczbę kroków i docelową liczbę okrążeń.

Podczas treningu na ekranie widać liczbę aktywnych samochodów oraz aktualny
krok generacji. `Esc` przerywa trening i wraca do menu. Po ukończeniu treningu
najlepszy genom jest zapisywany jako `winner.pkl`.

### Watch AI

Wczytuje `winner.pkl` i pokazuje przejazd najlepszego zapisanego genomu.

Opcja `AI sensors` w menu decyduje, czy pokazywać promienie czujników.
`R` resetuje przejazd po kraksie, a `Esc` wraca do menu.

Jeśli `winner.pkl` nie istnieje, program poprosi o wcześniejsze wytrenowanie
AI.

### Edit Track

Tryb edycji toru. Pozwala narysować własną pętlę i zapisać ją do
`track_layout.json`.

Sterowanie edytorem:

- lewy przycisk myszy - rysowanie linii środkowej toru,
- `Enter` - zapis toru,
- `C` - wyczyszczenie aktualnego szkicu,
- `D` - przywrócenie domyślnego toru,
- `[` albo `-` - zmniejszenie szerokości toru,
- `]` albo `+` - zwiększenie szerokości toru,
- `Esc` - powrót do menu.

## Tworzenie nowych torów

Tor jest zapisywany jako:

- `centerline` - lista punktów środka drogi,
- `track_width` - szerokość toru w pikselach.

Podczas rysowania edytor zbiera punkty kursora. Nowy punkt jest dodawany
dopiero wtedy, gdy jest oddalony od poprzedniego o co najmniej `6` pikseli.
Po zapisie projekt buduje z tych punktów zamkniętą pętlę.

Walidacja toru:

- szkic musi mieć co najmniej `6` punktów wejściowych,
- jeśli koniec nie jest blisko początku, pierwszy punkt jest dopinany na
  końcu, aby zamknąć pętlę,
- całkowita długość toru musi mieć co najmniej `400` pikseli,
- liczba próbek po przeliczeniu nie może spaść poniżej `24`,
- szerokość toru jest ograniczana do zakresu `50 - 140` pikseli.

Po walidacji linia jest próbkowana ponownie co około `12` pikseli. Maksymalnie
powstaje `260` punktów. Dzięki temu tor ma równomierną reprezentację niezależnie
od tego, jak szybko był rysowany myszą.

Z przeliczonego toru generowane są:

- maska kolizji,
- widoczna powierzchnia toru,
- linia mety,
- checkpointy,
- pozycje startowe dla graczy i AI.

Checkpointy są rozmieszczane automatycznie wzdłuż linii środkowej toru.
Domyślnie projekt używa `6` checkpointów. Po zapisaniu toru jest on od razu
używany przez wszystkie tryby, w tym trening AI.

## Pliki zapisywane przez aplikację

- `track_layout.json` - aktualny tor utworzony w edytorze.
- `winner.pkl` - najlepszy genom zapisany po treningu.

Zmiana toru wpływa na kolejne uruchomienia gry i treningu. Jeśli AI było
trenowane na starym torze, po zmianie układu trasy zapisany zwycięzca może
jeździć gorzej i zwykle warto uruchomić trening ponownie.
