# J.A.R.V.I.S. v1

Prima versiune a asistentului vocal personal.

## Ce face

- Ascultă microfonul.
- Execută comenzile numai dacă primul cuvânt este „Jarvis”.
- „Jarvis, ești aici?” -> „Yes, sir.”
- Spune ora.
- Deschide Telegram.
- Deschide aplicații Windows simple: Notepad, Calculator, Paint, Explorer.
- Caută pe Google și deschide rezultatele în browser.
- Deschide căutarea pentru vreme.
- Are o fereastră pe ecran unde afișează comenzile și activitatea.
- Pentru o operație care durează mai mult de 7 secunde, spune că încă lucrează, apoi repetă mesajul la aproximativ 9 secunde.

## Instalare

Recomandat: Windows + Python 3.11.

În terminalul VS Code, din folderul proiectului:

    pip install -r requirements.txt

Apoi:

    python main.py

## Exemple de comenzi

    Jarvis, ești aici
    Jarvis, spune ora
    Jarvis, deschide Telegram
    Jarvis, deschide calculatorul
    Jarvis, deschide Notepad
    Jarvis, caută pe Google cum funcționează un motor diesel
    Jarvis, caută vremea în Chișinău

## Important

Comanda:

    deschide Telegram

fără „Jarvis” NU este executată.

Recunoașterea vocală folosește serviciul Google Speech Recognition, deci pentru recunoașterea vocii este necesară conexiune la internet.
Text-to-speech (vocea lui JARVIS) folosește pyttsx3.
