
#########################
# ---   Imports     --- #
#########################

import telepot
import time
import json
import pickle
import hashlib
from cProfile import runctx
from telepot.loop import MessageLoop
from constants import Constants as const

# Eigene
import debts

# Temporär?
import pprint



###############################################
# ---   Globale Variablen & Konstanten    --- #
###############################################

# --- Konstanten --- #

MO_NULL = "kein Modus"
MO_NORMAL = "normal"
MO_PASSWORT = "passwort"
MO_SCHLÜSSEL = "schlüssel"
MO_EINKÄUFE = "einkauf"
MO_GRUPPEN = "gruppen"
MO_ADD_INFO_LINK = "link hinzufügen"
MO_ADD_INFO_TEXT = "info hinzufügen"
MO_SCHULDENZAHLEN = "schulden zahlen"
MO_SCHULDENMACHEN = "schulden machen"
MO_SPRINGER ="springer"
MO_ALL = "all"

SUPPORTTEAM = "@FrtZgwL und @MauriceHaug"
PASSWORT = ""
ADMIN_PASSWORT = ""
TOKEN = ""

#--- Menues ---#

ME_HAUPT = "haupt"

ME_SCHLÜSSEL = "schlüssel"

ME_SCHULDEN = "schulden"
ME_SCHULDENBEGLEICHEN = "schulden/begleichen"

ME_EINKAUFSLISTE = "einkaufsliste"
ME_ARTIKELENTFERNEN = "einkaufsliste/entfernen"

ME_GRUPPEN= "gruppen"

ME_INFO = "info"
ME_INFOLÖSCHEN = "info/löschen"

ME_TÜR = "tür"




# --- Variablen --- #

menüs = {}
pp = pprint.PrettyPrinter(indent=2)

display_message = {}
users = {}
data = {}
infotext = ""
bank = debts.Bank()



###########################################
# ---   json Datein barbeiten/laden   --- #
###########################################

with open("Daten/menüs.json", "r") as f:
    menüs = json.load(f)

with open("Daten/users.json", "r") as f:
    users = json.load(f)

with open("Daten/data.json", "r") as f:
    data = json.load(f)

with open("Daten/config.json", "r") as f:
    config = json.load(f)
    if config["token"] == "":
        sys.exit("No token defined. Define it in a file called token.txt.")
    if config["passwort"] == "":
        print("WARNING: Empty Password for registering to use the bot." +
              " It could be dangerous, because anybody could use this bot" +
              " and forward messages to the channels associated to it")
    SUPPORTTEAM = config["supportteam"]
    PASSWORT = config["passwort"]
    ADMIN_PASSWORT = config["adminpasswort"]
    TOKEN = config["token"]

with open("Daten/schulden.bin", "rb") as f:
    bank = pickle.load(f)

#########################
# ---   Funktionen  --- #
#########################

def error(chat_id):

    users[str(chat_id)]["modus"] = MO_NORMAL
    users[str(chat_id)]["menue"] = ME_HAUPT
    save("Daten/users.json", users)

    display_message = bot.sendMessage(chat_id, "Ups! Irgendwas ist schiefgelaufen! Tippe auf \"Hilfe\" oder \"Hauptmenü\", um Hilfe zu erhalten oder zum Hauptmenü zurück zu gehen.", reply_markup=json.dumps(menüs["error"]))

def save(pfad, obj):
    with open(pfad, "w") as f:
        f.write(json.dumps(obj, indent=2, sort_keys=True))

def pickle_save(pfad, obj):
    with open(pfad, "wb") as f:
        pickle.dump(obj, f)

def build_name(msg):
    if msg["chat"]["type"] == "private":
        return msg["from"]["first_name"] + (" " + msg["chat"]["last_name"] if "last_name" in msg["chat"] else "")
    else:
        return msg["chat"]["title"]

def build_button_menu(items, footer=None, identifier=""):
    menu = "{\"inline_keyboard\":["

    for item in items:
        menu = menu + "[{\"text\":\"" + item + "\",\"callback_data\":\"" + identifier + item + "\"}],"

    if footer:
        for row in footer:
            menu += "["
            for button in row:
                if len(button[0]) == 1:
                    menu += "{\"text\":\"" + button + "\","
                    menu += "\"callback_data\":\"" + button + "\"},"
                    break

                menu += "{\"text\":\"" + button[0] + "\","
                menu += "\"callback_data\":\"" + button[1] + "\"},"
            menu = menu[:-1]
            menu += "],"
        menu = menu[:-1]
        menu += "]}"
    else:
        menu = menu[:-1]
        menu += "]}"

    return menu

def build_keyboard_menu(menu, resize_keyboard=True):
    """Takes a 2D Array with menu buttons
    Returns a json serialized string of a ReplyKeyboardMarkup object"""

    if resize_keyboard:
        string = "{\"keyboard\":" + json.dumps(menu) + ","
        string += "\"resize_keyboard\":true}"
    else:
        string = "{\"keyboard\":" + json.dumps(menu) + "}"
    return string

def build_remove_menu():
    """returns a json serialized ReplyKeyboardRemove object"""
    return "{\"remove_keyboard\":true}"

def build_shoplist_text(data):
    """returns a user-readable string with all the items on the shoplist."""

    list_text = "Auf der Einkaufsliste stehen:"

    for item in data["einkaufsliste"]:
        list_text = list_text + "\n - " + item

    return list_text

#################################################
# ---   FUNKTIONEN FÜR BUTTON INTERAKTION   --- #
#################################################

def key(chat_id, msg_id, callback_id):
    global users
    bot.answerCallbackQuery(callback_id)

    users[str(chat_id)]["menue"] = ME_SCHLÜSSEL
    save("Daten/users.json", users)

    schlüssel_text = "Die aktuellen Schlüsselträger sind: Das Faust"

    for user in users:
        if users[user]["is_schlüsselträger"]:
            schlüssel_text = schlüssel_text + ", " + users[user]["name"]

    if users[str(chat_id)]["is_schlüsselträger"]:
        display_message = bot.editMessageText((chat_id, msg_id), schlüssel_text, reply_markup=json.dumps(menüs["habschlüssel"]))
    else:
        display_message = bot.editMessageText((chat_id, msg_id), schlüssel_text, reply_markup=json.dumps(menüs["habkeinenschlüssel"]))

def addkey(chat_id, msg_id, callback_id):
    global users
    warning = ""

    anzahl_schlüsselträger = 0
    for user in users:
        if users[user]["is_schlüsselträger"]:
            anzahl_schlüsselträger += 1

    if anzahl_schlüsselträger >= 4:
        warning = "\nSo viele Schlüssel gibt es nicht! Erinnere den letzten Schlüsselträger daran, sich zu entfernen."

    users[str(chat_id)]["is_schlüsselträger"] = True
    save("Daten/users.json", users)

    bot.answerCallbackQuery(callback_id, text="Du wurdest als Schlüsselträger hinzugefügt" + warning, show_alert=True)


    mainmenu(chat_id, msg_id, callback_id)

def rmkey(chat_id, msg_id, callback_id):
    global users

    users[str(chat_id)]["is_schlüsselträger"] = False
    users[str(chat_id)]["modus"] = MO_NORMAL
    users[str(chat_id)]["menue"] = ME_SCHLÜSSEL
    save("Daten/users.json", users)

    bot.answerCallbackQuery(callback_id, text="Du wurdest als Schlüsselträger entfernt", show_alert=True)

    mainmenu(chat_id, msg_id, callback_id)

def msgkey(chat_id, msg_id, callback_id):
    global users
    bot.answerCallbackQuery(callback_id)

    users[str(chat_id)]["modus"] = MO_SCHLÜSSEL
    save("Daten/users.json", users)

    display_message = bot.editMessageText((chat_id, msg_id), "Schick mir bitte deine Nachricht, dann leite ich sie weiter...", reply_markup=json.dumps(menüs["nachrichten"]))

def all(chat_id, msg_id, from_id):
    global users

    if users[str(from_id)]["is_admin"]:

        users[str(chat_id)]["modus"] = MO_ALL
        save("Daten/users.json", users)

        display_message = bot.editMessageText((chat_id, msg_id), "Bitte sende mir die Nachricht zu, die ich weitergeleitet soll.", reply_markup=json.dumps(menüs["nachrichten"]))
    else:
        bot.sendMessage(chat_id, "Nur admins können an alle eine Nachricht schreiben.", reply_markup=json.dumps(menüs["nachrichten"]))




#############################################
# ---   FUNKTIONEN FÜR CHAT-INTERAKTION --- #
#############################################

def chat_passwort(chat_id, txt):
    global data
    global display_message

    if hashlib.sha256(txt.encode()).hexdigest() == PASSWORT:
        users[str(chat_id)]["is_allowed"] = True
        users[str(chat_id)]["modus"] = MO_NORMAL
        save("Daten/users.json", users)

        bot.sendMessage(chat_id, "Du wurdest erfolgreich als Nutzer hinzugefügt! Viel Spaß!")
        display_message = bot.sendMessage(chat_id, "Hauptmenü", reply_markup=json.dumps(menüs["haupt"]))
    else:
        display_message = bot.sendMessage(chat_id, "Bitte gibt das korrekte Passwort ein. Wenn du nicht weiter weißt, wende dich an " + SUPPORTTEAM + ".")



def chat_gruppen(chat_id, txt, msg_id):
    global display_message
    global data

    try:
        bot.forwardMessage(users[str(chat_id)]["forward_to"], chat_id, msg_id)
        if users[str(chat_id)]["forward_to"] > 0: # only for private chats
            bot.sendMessage(users[str(chat_id)]["forward_to"], "Hauptmenü", reply_markup=json.dumps(menüs["nachrichten"]))

        display_message = bot.sendMessage(chat_id, "Deine Nachricht wurde erfolgreich versendet.", reply_markup=json.dumps(menüs["nachrichten"]))
    except telepot.exception.BotWasKickedError:
        display_message = bot.sendMessage(chat_id, "Sorry, aber die Gruppe gibt es nicht mehr. Bitte melde dich bei " + SUPPORTTEAM + ".", reply_markup=json.dumps(menüs["nachrichten"]))

def chat_springer(chat_id, txt, msg_id):
    global display_message

    there_are_jumpers = False

    for id in users:
        if users[id]["is_springer"]:
            there_are_jumpers = True

            bot.forwardMessage(int(id), chat_id, msg_id)
            bot.sendMessage(int(id), "Hauptmenü", reply_markup=json.dumps(menüs["nachrichten"]))

    if there_are_jumpers:
        display_message = bot.sendMessage(chat_id, "Deine Nachricht wurde erfolgreich versendet.", reply_markup=json.dumps(menüs["nachrichten"]))

    else:
        display_message = bot.sendMessage(chat_id, "Es gibt im Moment kein Springer", reply_markup=json.dumps(menüs["nachrichten"]))

def chat_schuldenzahlen(chat_id, txt):
    global users
    global display_message
    aktuelle_schulden = users[str(chat_id)]["schulden"]
    #aktuelle_schulden = round(aktuelle_schulden, 2)

    try:
        betrag = abs(float(txt.replace(",", ".").replace("€", "")))
        #betrag = round(betrag, 2)

        if aktuelle_schulden - betrag < 0:
            display_message = bot.sendMessage(chat_id, "Du schuldest dem Faust " + str(aktuelle_schulden).replace(".", ",") + "€. Du kannst nicht mehr zurückzahlen, als du dem Faust schuldest. Bitte sende mir den zurückgezahlten Betrag als Kommazahl", parse_mode="Markdown", reply_markup=json.dumps(menüs["nachrichten"]))
        else:
            users[str(chat_id)]["schulden"] = round(aktuelle_schulden - betrag, 2)
            users[str(chat_id)]["modus"] = MO_SCHULDENZAHLEN
            save("Daten/users.json", users)

            display_message = bot.sendMessage(chat_id, "Von deiner Schuldenliste wurden " + str(betrag).replace(".", ",") + "€ gestrichen. Du schuldest dem Faust noch " + str(round(aktuelle_schulden-betrag,2)).replace(".", ",") + "€", parse_mode="Markdown", reply_markup=json.dumps(menüs["schuldenbegleichen"]))

    except ValueError as e:
        display_message = bot.sendMessage(chat_id, "Bitte sende mir deine Schulden entweder als ganze Zahl _10_, bzw. Kommazahl im Format:  _1,2_ oder _1.2_. Deine aktuellen Schulden sind: _" + str(aktuelle_schulden).replace(".", ",") + "€_", parse_mode="Markdown", reply_markup=json.dumps(menüs["nachrichten"]))

def chat_schuldenmachen(chat_id, txt):
    global users
    global display_message
    aktuelle_schulden = users[str(chat_id)]["schulden"]

    try:
        betrag = abs(float(txt.replace(",", ".").replace("€", "")))

        users[str(chat_id)]["schulden"] = round(aktuelle_schulden + betrag, 2)
        users[str(chat_id)]["modus"] = MO_SCHULDENMACHEN
        save("Daten/users.json", users)

        display_message = bot.sendMessage(chat_id, "Zu deinen Schulden wurden " + str(betrag).replace(".", ",") + "€ addiert. Du schuldest dem Faust noch " + str(aktuelle_schulden+betrag).replace(".", ",") + "€", parse_mode="Markdown", reply_markup=json.dumps(menüs["schulden"]))

    except ValueError as e:
        display_message = bot.sendMessage(chat_id, "Bitte sende mir deine Schulden entweder als ganze Zahl _10_, bzw. Kommazahl im Format:  _1,2_ oder _1.2_. Deine aktuellen Schulden sind: _" + str(aktuelle_schulden).replace(".", ",") + "€_", parse_mode="Markdown", reply_markup=json.dumps(menüs["nachrichten"]))

def chat_schluessel(chat_id, msg_id):
    # Nachricht an alle Schlüsselträger senden
    for user in users:
        if users[user]["is_schlüsselträger"]:
            bot.forwardMessage(int(user), chat_id, msg_id)
            display_message = bot.sendMessage(int(user), "Klick auf _Hauptmenü_, um zurück zum Hauptmenü zu kommen", parse_mode="Markdown", reply_markup=json.dumps(menüs["nachrichten"]))
        bot.sendMessage(chat_id, "Deine Nachricht wurde erfolgreich weitergeleitet.", reply_markup=json.dumps(menüs["nachrichten"]))

def chat_normal(chat_id, txt, msg):
    global display_message

    if txt[0] == "#":
        txt_split =txt.strip().split(" ")
        i= 0
        tags = []
        while i < len(txt_split) and txt_split[i][0] == "#":
            tags.append(txt_split[i].lower())
            i+=1
        if i != len(txt_split) or "reply_to_message" in msg:
            approved = []
            rejected = []
            for tag in tags:
                if tag in data["chats"]:
                    if data["chats"][tag][0] !=str(chat_id):
                        group_id = data["chats"][tag][0]
                        group_name = data["chats"][tag][1]

                        try:
                            bot.forwardMessage(group_id, chat_id, msg["message_id"])
                            bot.sendMessage(chat_id, "Deine Nachricht wurde erfolgreich weitergeleitet an <i>" + group_name + "</i>", parse_mode="HTML", reply_markup=json.dumps(menüs["nachrichten"]))
                            if "reply_to_message" in msg:
                                bot.forwardMessage(group_id, chat_id, msg["reply_to_message"]["message_id"])
                                bot.sendMessage(chat_id, "Deine Nachricht wurde erfolgreich weitergeleitet an <i>" + group_name + "</i>", parse_mode="HTML", reply_markup=json.dumps(menüs["nachrichten"]))
                            approved.append(group_name)
                        except telepot.exception.BotWasKickedError:
                            rejected.append(tag)
                else:
                    rejected.append(tag)
            if len(rejected) > 0:
                bot.sendMessage(chat_id,"Ich konnte leider an folgende Tags keine Nachricht senden: <i>" + ", ".join(rejected) + "</i>\nFalls der Tag trotzdem in Gruppen angezeigt wird, wurde die Gruppe gelöscht bitte melde dich in diesem Fall bei " + SUPPORTTEAM + "." , parse_mode="HTML", reply_markup=json.dumps(menüs["error"]))
        else:
            # Fehler, weil leere Nachricht mit Tags
            bot.sendMessage(chat_id, "Du kannst keine leeren Nachrichten senden. Bitte sende mir eine Nachricht mit den Tags", reply_markup=json.dumps(menüs["error"]))
    else:
        # Fehler, weil irgend ne Nachricht
        error(chat_id)

def chat_send_all(chat_id, msg_id, msg):
    global display_message

    benutzer = []
    abgelehnte_benutzer = []

    for user in users:
        name = users[user]["name"]
        try:
            bot.forwardMessage(int(user), chat_id, msg["message_id"])
            display_message = bot.sendMessage(int(user), "Klick auf _Hauptmenü_, um zurück zum Hauptmenü zu kommen", parse_mode="Markdown", reply_markup=json.dumps(menüs["nachrichten"]))

            benutzer.append(name)
        except telepot.exception.TelegramError:
            abgelehnte_benutzer.append(name)

    display_message = bot.sendMessage(chat_id, "Deine Nachricht wurde erfolgreich an <i>" + ", ".join(benutzer) + " </i> weitergeleitet. Jetzt  kommen alle Namen an die es nicht geklappt hat:" + ", ".join(abgelehnte_benutzer), parse_mode="HTML", reply_markup=json.dumps(menüs["nachrichten"]))



def handle(msg):
    global display_message
    global users
    global data

    flavor = telepot.flavor(msg)


##################################
# ---   TELEGRAM BEFEHLE    ---- #
##################################

    if flavor == "chat":
        chat_id = msg["chat"]["id"]
        from_id = msg["from"]["id"] # Das muss noch konsequenter umgesetzt werden
        txt = msg["text"]

        if "/start" == txt[:6]:
            if msg["chat"]["type"] != "private":
                bot.sendMessage(chat_id, "/start geht nur in Privatchats.")

            else:
                if str(chat_id) not in users:
                    users[str(chat_id)] = {
                    "name":build_name(msg),
                    "modus":MO_PASSWORT,
                    "menue":ME_HAUPT,
                    "current_group":"",
                    "schulden":0.0,
                    "is_allowed":False,
                    "is_finanzen":False,
                    "is_einkauf":False,
                    "is_admin":False,
                    "is_schlüsselträger":False,
                    "is_springer":False
                    }
                    save("Daten/users.json", users)

                    bot.sendMessage(chat_id, "Hi, " + build_name(msg) + "!\nGib bitte das Passwort ein, um Zugriff zu erhalten. Falls du das Passwort nicht weiß, schreib eine Nachricht an " + SUPPORTTEAM + ".")

                elif users[str(chat_id)]["is_allowed"]:
                    users[str(chat_id)]["modus"] = MO_NORMAL
                    users[str(chat_id)]["menue"] = ME_HAUPT
                    save("Daten/users.json", users)

                    display_message = bot.sendMessage(chat_id, "Hauptmenü", reply_markup=json.dumps(menüs["haupt"]))

                else:
                    display_message = bot.sendMessage(chat_id, "Hey, du bist leider noch nicht als Nutzer hinzugefügt. Gib bitte erst das richtige Passwort ein. Bei Problemen kanns du dich immer an " + SUPPORTTEAM + " wenden")

        # elif "/cheat" == txt[:len("/cheat")]:
        #
        #     chats = {}
        #     global data
        #
        #     with open("Daten/chats.json", "r") as f:
        #         chats = json.load(f)
        #
        #     for tag in chats:
        #         id = chats[tag]["id"]
        #         name = chats[tag]["name"]
        #
        #         data["chats"][tag] = [int(id), name] #TODO NOW
        #
        #     save("Daten/data.json", data)

        elif "/help" == txt[:5] or "/?" == txt[:2]:
            if str(chat_id) in users:
                if users[str(chat_id)]["is_allowed"]:
                    help_chat(chat_id)
                else:
                    bot.sendMessage(chat_id, "Nur registrierte Nutzer können diese Funktion nutzen. Du musst zuerst das korrekte Passwort eingeben.")
            else:
                bot.sendMessage(chat_id, "Nur registrierte Nutzer können diese Funktion nutzen. Du musst zuerst das korrekte Passwort eingeben.")

        elif "/admin" == txt[:6]:
            if msg["chat"]["type"] != "private":
                bot.sendMessage(chat_id, "/admin geht nur in Privatchats.")

            else:
                if ADMIN_PASSWORT == hashlib.sha256(txt[7:].encode()).hexdigest():
                    users[str(msg["from"]["id"])]["is_admin"] = True
                    save("Daten/users.json", users)

                    display_message = bot.sendMessage(chat_id, "Du wurdest als Admin hinzugefügt!")
                else:
                    display_message = bot.sendMessage(chat_id,
                    "Falsches Passwort!")

        elif "/add" == txt[:4]:
            if not users[str(from_id)]["is_admin"]:
                bot.sendMessage(chat_id, "Nur admins können neue Gruppen hinzufügen.")

            elif msg["chat"]["type"] != "group":
                bot.sendMessage(chat_id, "\"/add\" ist nur dazu da, um _normale Gruppen_ hinzuzufügen.", parse_mode="Markdown")

            else:
                # Befehl formal überprüfen
                if len(txt) < 5:
                    bot.sendMessage(chat_id, "Du musst einen Tag für deine Gruppe angeben. Zum Beispiel so: _#meinegruppe_", parse_mode="Markdown",)
                elif txt[5] != "#":
                    bot.sendMessage(chat_id, "Jeder Tag muss mit einem \"#\" beginnen. Zum Beispiel so: _#meinegruppe_", parse_mode="Markdown")
                elif " " in txt[5:]:
                    bot.sendMessage(chat_id, "Tags dürfen nur aus einem Wort bestehen. Zum Beispiel so: _#meinegruppe_", parse_mode="Markdown")
                # Neue Gruppe hinzufügen
                else:
                    data["chats"][txt.lower()[5:]] = [chat_id, build_name(msg)]
                    save("Daten/data.json", data)

                    bot.sendMessage(chat_id, "_" + txt.lower()[5:] + "_ wurde als neue Gruppe hinzugefügt.", parse_mode="Markdown")

        elif "/debts" == txt[:6]:
            if (users[str(chat_id)]["is_admin"] | users[str(chat_id)]["is_finanzen"]):
                for id in users:
                    try:
                        bot.sendMessage(chat_id, users[id]["name"] + "\n" + bank.get_debts(int(id)))
                    except IndexError:
                        bot.sendMessage(chat_id, users[id]["name"] + "\n" "Keine Einträge+\n\n")
            else:
                bot.sendMessage(chat_id, "Sorry, aber du hast nicht das Recht, diese Funktion zu benutzen...\nDrück auf /start um den Bot zu starten.")

#######################################################
#           ---   CHAT INTERAKTION    --- #
#######################################################

        elif msg["chat"]["type"] == "private":
            # Wenn noch kein Nutzer, Fehlermeldung und rausschmeißen
            if str(msg["from"]["id"]) not in users:
                bot.sendMessage(msg["chat"]["id"], "Du bist noch nicht als Nutzer eingetragen. Starte den chat mit dem Bot durch \"/start\" und gib das Passwort ein.")
            else:
                modus = users[str(chat_id)]["modus"]

            # Variablen erstellen
            modus = 0
            menue = users[str(chat_id)]["menue"]

            # --- TASTATURBUTTON INTERAKTION --- #
            print(menue)

            button = txt

            # General buttons
            if button == "Hauptmenü":
                users[str(chat_id)]["menue"] = "Hauptmenü"
                save("Daten/users.json", users)

                display_message = bot.sendMessage(chat_id, "Hauptmenü", reply_markup=build_keyboard_menu(const.menu_main))

            elif button == "Hilfe":
                help_str = "Ich bin der Faustbot 2.0! Ich Bot ermögliche dir die Kommunikation zwischen den Gruppen im Café Faust und biete dazu viele weitere Funktionen.\n\nAm einfachsten bentzt du mich, indem du dich durch das Hauptmenü klickst, du kannst aber auch immer Nachrichten an die Gruppen senden, indem du mir eine Nachricht sendest, die mit dem Tag der Gruppe beginnt. Es gibt diese Gruppen: "

                for tag in data["chats"]:
                    help_str += tag + ", "
                help_str = help_str[:-2]

                help_str += "\n\nBei Fragen kannst du dich immer gerne an " + SUPPORTTEAM + " wenden."

                bot.sendMessage(chat_id, help_str, reply_markup=build_keyboard_menu(const.menu_basic, resize_keyboard=True))

            elif button == "Zurück": # TODO: Dopplungen überall! Kann man das nicht klüger machen?

                if menue == "Info/Anzeigen":
                    # TODO: Das ist das selbe wie der Hauptmenü-Button. Hier müssen wir also ein besseres System finden. Vielleicht auch unten auf Zurück-Buttons reagieren?
                    users[str(chat_id)]["menue"] = "Info"

                    bot.sendMessage(chat_id, "Tippe auf Zeilen, um Informationen zu erhalten.", reply_markup=build_keyboard_menu(const.menu_info_main))
                    users[str(chat_id)]["display_message"] = bot.sendMessage(chat_id, "Info", reply_markup=build_button_menu(data["infos"]))["message_id"]

                    save("Daten/users.json", users)

                elif menue == "Info/Entfernen":
                    # TODO: Das ist das selbe wie der Hauptmenü-Button. Hier müssen wir also ein besseres System finden. Vielleicht auch unten auf Zurück-Buttons reagieren?
                    users[str(chat_id)]["menue"] = "Info"

                    bot.sendMessage(chat_id, "Tippe auf Zeilen, um Informationen zu erhalten.", reply_markup=build_keyboard_menu(const.menu_info_main))
                    users[str(chat_id)]["display_message"] = bot.sendMessage(chat_id, "Info", reply_markup=build_button_menu(data["infos"]))["message_id"]

                    save("Daten/users.json", users)

                elif menue == "Einkaufsliste/Entfernen":
                    # TODO: Das ist das selbe wie der Hauptmenü-Button. Hier müssen wir also ein besseres System finden. Vielleicht auch unten auf Zurück-Buttons reagieren?
                    users[str(chat_id)]["menue"] = "Einkaufsliste"
                    save("Daten/users.json", users)

                    bot.sendMessage(chat_id, build_shoplist_text(data), reply_markup=build_keyboard_menu(const.menu_add_remove), parse_mode="Markdown")

                elif menue == "schulden/begleichen":
                    debt(chat_id, msg_id, callback_id)

                elif menue == "info/löschen":
                    info(chat_id, msg_id, callback_id)

            # Menüs
            elif menue == "Hauptmenü":

                if button == "Gruppen":
                    users[str(chat_id)]["menue"] = "Gruppen"
                    save("Daten/users.json", users)

                    display_message = bot.sendMessage(chat_id, "Gruppen", reply_markup=build_keyboard_menu(const.menu_basic))
                    display_message = bot.sendMessage(chat_id, "Tippe auf die Gruppe um ihnen eine Nachricht zu senden", reply_markup=build_button_menu(data["chats"], const.footer_group_main, "chat"))

                elif button == "Info":
                    users[str(chat_id)]["menue"] = "Info"

                    bot.sendMessage(chat_id, "Tippe auf Zeilen, um Informationen zu erhalten.", reply_markup=build_keyboard_menu(const.menu_info_main))
                    users[str(chat_id)]["display_message"] = bot.sendMessage(chat_id, "Info", reply_markup=build_button_menu(data["infos"]))["message_id"]

                    save("Daten/users.json", users)

                elif button == "Schlüssel":
                    schlüssel_text = "Die aktuellen Schlüsselträger sind: Das Faust"

                    for user in users:
                        if users[user]["is_schlüsselträger"]:
                            schlüssel_text = schlüssel_text + ", " + users[user]["name"]

                    users[str(chat_id)]["menue"] = "Schlüssel"
                    save("Daten/users.json", users)

                    if users[str(chat_id)]["is_schlüsselträger"]:
                        bot.sendMessage(chat_id, schlüssel_text, reply_markup=build_keyboard_menu(const.menu_has_key))
                    else:
                        bot.sendMessage(chat_id, schlüssel_text, reply_markup=build_keyboard_menu(const.menu_has_no_key))

                elif button == "Schulden":
                    users[str(chat_id)]["menue"] = "Schulden"
                    save("Daten/users.json", users)

                    bot.sendMessage(chat_id, "Du schuldest dem Faust jetzt " + str(users[str(chat_id)]["schulden"]).replace(".", ",") + "€.\n" + const.mitarbeiterpreise, reply_markup=build_keyboard_menu(const.menu_make_debts))

                elif button == "Einkaufsliste":
                    users[str(chat_id)]["menue"] = "Einkaufsliste"
                    save("Daten/users.json", users)

                    bot.sendMessage(chat_id, build_shoplist_text(data), reply_markup=build_keyboard_menu(const.menu_add_remove), parse_mode="Markdown")

                elif button == "tür":
                    door(chat_id, msg_id, callback_id)

                else:
                    error(chat_id)

            elif menue[:4] == "Info":
                global infotext # TODO: Find a better solution than this.

                # Submenus
                if menue == "Info/Hinzufügen/Name":
                    # Erster Durchlauf: Name und Typ eingeben
                    data["infos"][button] = ["TEXT", "...Leere Information..."]
                    save("Daten/data.json", data)
                    # Menü für zweiten Durchlauf ändern
                    users[str(chat_id)]["menue"] = "Info/Hinzufügen/Text"
                    users[str(chat_id)]["temp"] = button
                    save("Daten/users.json", data)

                    infotext = button

                    # Text eingabe auffordern
                    bot.sendMessage(chat_id, "Schick mir jetzt bitte die Informationen, die du speichern willst", reply_markup=build_remove_menu())

                elif menue == "Info/Hinzufügen/Text":
                    if infotext in data["infos"]:
                        # Zweiter Durchlauf: Text eingeben
                        name = users[str(chat_id)]["temp"]
                        data["infos"][name][1] = button
                        save("Daten/data.json", data)

                        bot.sendMessage(chat_id, "Die neuen Informationen wurden unter dem Namen _" + infotext + "_ gespeichert.", parse_mode="Markdown", reply_markup=build_keyboard_menu(const.menu_main))

                        infotext = ""
                        users[str(chat_id)]["menue"] = "Hauptmenü"
                        save("Daten/users.json", users)

                    # TODO: Brauchen wir das? Funktioniert das?
                    else:
                        error(chat_id)

                # Buttons
                if button == "Hinzufügen":
                    users[str(chat_id)]["menue"] = "Info/Hinzufügen/Name"
                    save("Daten/users.json", users)

                    display_message = bot.sendMessage(chat_id, "Schick mir bitte den Namen unter dem du deine Infos speichern willst.", reply_markup=build_remove_menu())

                elif button == "Entfernen":
                    users[str(chat_id)]["menue"] = "Info/Entfernen"

                    bot.sendMessage(chat_id, "Tippe Buttons an, um Informationen zu löschen.", reply_markup=build_keyboard_menu(const.menu_back_main))
                    users[str(chat_id)]["display_message"] = bot.sendMessage(chat_id, "Informationen:", reply_markup=build_button_menu(data["infos"]))["message_id"]

                    save("Daten/users.json", users)

            elif menue == "Gruppen/Senden":
                try:
                    bot.forwardMessage(users[str(chat_id)]["forward_to"], chat_id, msg["message_id"])

                    bot.sendMessage(chat_id, "Deine Nachricht wurde erfolgreich versendet.", reply_markup=build_keyboard_menu(const.menu_main))
                except telepot.exception.BotWasKickedError:
                    display_message = bot.sendMessage(chat_id, "Sorry, aber die Gruppe gibt es nicht mehr. Bitte melde dich bei " + SUPPORTTEAM + ".", reply_markup=build_keyboard_menu(const.menu_basic))
                finally:
                    users[str(chat_id)]["menue"] = "Hauptmenü"

            elif menue == "Schlüssel":

                if button =="Hinzufügen":
                    warning = None

                    anzahl_schlüsselträger = 0
                    for user in users:
                        if users[user]["is_schlüsselträger"]:
                            anzahl_schlüsselträger += 1

                    if anzahl_schlüsselträger >= 4:
                        warning = "\nSo viele Schlüssel gibt es nicht! Erinnere den letzten Schlüsselträger daran, sich zu entfernen."

                    users[str(chat_id)]["is_schlüsselträger"] = True
                    save("Daten/users.json", users)

                    if warning:
                        bot.sendMessage(chat_id, warning)
                    bot.sendMessage(chat_id, "Du wurdest als Schlüsselträger hinzugefügt", reply_markup=build_keyboard_menu(const.menu_has_key))

                elif button == "Entfernen":
                    users[str(chat_id)]["is_schlüsselträger"] = False
                    save("Daten/users.json", users)

                    bot.sendMessage(chat_id, "Du wurdest als Schlüsselträger entfernt", reply_markup=build_keyboard_menu(const.menu_has_no_key))

                elif button == "Nachricht":
                    msgkey(chat_id, msg_id, callback_id)

                else:
                    error(chat_id)

            elif menue[:8] == "Schulden":

                if button == "Schulden begleichen":
                    bot.sendMessage(chat_id, "Du schuldest dem Faust. " + str(users[str(chat_id)]["schulden"]) + "€. Schick mir den Betrag, den du in die Kasse gezahlt hast, oder tipp auf \"Alles zahlen\"", reply_markup=build_keyboard_menu(const.menu_pay_debts))

                elif button == "Schulden machen":
                    bot.sendMessage(chat_id, "Du schuldest dem Faust jetzt " + str(users[str(chat_id)]["schulden"]).replace(".", ",") + "€.\n" + const.mitarbeiterpreise, reply_markup=build_keyboard_menu(const.menu_make_debts))

                elif button == "Alles zahlen":
                    users[str(chat_id)]["schulden"] = 0
                    save("Daten/users.json", users)

                    bot.sendMessage(chat_id, "Du schuldest dem Faust jetzt " + str(users[str(chat_id)]["schulden"]).replace(".", ",") + "€.\n" + const.mitarbeiterpreise, reply_markup=build_keyboard_menu(const.menu_make_debts))

                else:
                    try: # Try to interpret message-text as debts
                        betrag = float(button.replace(",", ".").replace("€", ""))

                        users[str(chat_id)]["schulden"] = round(users[str(chat_id)]["schulden"] + betrag, 2)
                        save("Daten/users.json", users)

                        bot.sendMessage(chat_id, "Du schuldest dem Faust jetzt " + str(users[str(chat_id)]["schulden"]).replace(".", ",") + "€.\n" + const.mitarbeiterpreise, reply_markup=build_keyboard_menu(const.menu_make_debts))
                    except ValueError:
                        bot.sendMessage(chat_id, "Sorry, das versteh ich nicht... Sende mir bitte Beträge von Schulden. Also sowas wie: \"21.5\" oder \"10€\"\n" + const.mitarbeiterpreise)

            # TODO: Er solltes auch blicken, wenn man ihm im Obermenü Artikel schickt, ohne unter "Einkaufsliste/Hinzufügen" zu sein.
            elif menue[:13] == "Einkaufsliste":

                if menue[:24] == "Einkaufsliste/Hinzufügen":
                    artikel = txt + " (von " + users[str(chat_id)]["name"] + ")"

                    data["einkaufsliste"].append(artikel)
                    save("Daten/data.json", data)
                    users[str(chat_id)]["menue"] = "Einkaufsliste"
                    save("Daten/users.json", users)

                    bot.sendMessage(chat_id, "_" + txt + "_ wurde zur Einkaufsliste hinzugefügt.", parse_mode="Markdown")
                    bot.sendMessage(chat_id, build_shoplist_text(data), reply_markup=build_keyboard_menu(const.menu_add_remove))

                elif button == "Hinzufügen":
                    users[str(chat_id)]["menue"] = "Einkaufsliste/Hinzufügen"
                    save("Daten/users.json", users)

                    bot.sendMessage(chat_id, "Schick mir bitte deine Einkaufswünsche, ich schreibe sie auf die Liste...", reply_markup=build_remove_menu())

                elif button == "Entfernen":
                    users[str(chat_id)]["menue"] = "Einkaufsliste/Entfernen"
                    save("Daten/users.json", users)

                    bot.sendMessage(chat_id, "Welche Artikel willst du entfernen?", reply_markup=build_keyboard_menu(const.menu_back_main))
                    users[str(chat_id)]["display_message"] = bot.sendMessage(chat_id, "Tippe Buttons an, um Artikel zu entfernen", reply_markup=build_button_menu(data["einkaufsliste"], const.footer_shoplist_delete))["message_id"]

                else: # TODO: Dopplung mit "Einkaufsliste/Hinzufügen"
                    artikel = txt + " (von " + users[str(chat_id)]["name"] + ")"

                    data["einkaufsliste"].append(artikel)
                    save("Daten/data.json", data)
                    users[str(chat_id)]["menue"] = "Einkaufsliste"
                    save("Daten/users.json", users)

                    bot.sendMessage(chat_id, "_" + txt + "_ wurde zur Einkaufsliste hinzugefügt.", parse_mode="Markdown")
                    bot.sendMessage(chat_id, build_shoplist_text(data), reply_markup=build_keyboard_menu(const.menu_add_remove))

            elif menue[:4] == "info":
                if showinfo(chat_id, msg_id, callback_id, button):
                    pass

                elif menue[:12] == "info/löschen":
                    if deleteinfo(chat_id, msg_id, callback_id, button):
                        pass
                    else:
                        error(chat_id)

                elif button == "infolöschen":
                    dellinfo(chat_id, msg_id, callback_id)

                elif button == "infotexthinzufügen":
                    addinfo(chat_id, msg_id, callback_id, msg)

                else:
                    error(chat_id)

            elif menue == "tür":

                if button == "türzu":
                    closedoor(chat_id, msg_id, callback_id)

                elif button == "türoffen":
                    opendoor(chat_id, msg_id, callback_id)

                else:
                    error(chat_id)

        else:
            error(chat_id)




            # --- ANTWORTEN IN PRIVATCHATS ---- #

            if modus == MO_PASSWORT:
                chat_passwort(chat_id, txt)

            elif modus == MO_NORMAL:
                chat_normal(chat_id, txt, msg)

            elif modus == MO_GRUPPEN:
                chat_gruppen(chat_id, txt, msg["message_id"])

            elif modus == MO_SPRINGER:
                chat_springer(chat_id, txt, msg["message_id"])

            elif modus == MO_SCHULDENZAHLEN: # TODO zu viel weg + negativ
                chat_schuldenzahlen(chat_id, txt)

            elif modus == MO_SCHULDENMACHEN:
                chat_schuldenmachen(chat_id, txt)

            elif modus == MO_SCHLÜSSEL:
                chat_schluessel(chat_id, msg["message_id"])

            elif modus == MO_EINKÄUFE:
                chat_einkaeufe(chat_id, txt)

            elif modus == MO_ADD_INFO_TEXT:
                chat_add_info(chat_id, txt)

            elif modus == MO_ALL:
                chat_send_all(chat_id, msg["message_id"], msg)





########################################################
            # ---   BUTTON INTERAKTION  --- #
########################################################

    elif flavor == "callback_query":
        button = msg["data"]
        msg_id = msg["message"]["message_id"]
        chat_id = msg["message"]["chat"]["id"]
        callback_id = msg["id"]
        menue = users[str(chat_id)]["menue"]



        # elif menue[:13] == "einkaufsliste":
        #
        #     if menue[:23] == "einkaufsliste/entfernen":
        #         if dellitem(chat_id, msg_id, callback_id, button):
        #             pass
        #
        #         elif button == "alleslöschen":
        #             dellshoplist(chat_id, msg_id, callback_id)
        #
        #         else:
        #             error(chat_id)
        #
        #     elif button == "hinzufügen":
        #         addshoplist(chat_id, msg_id, callback_id)
        #
        #     elif button == "entfernen":
        #         clearshoplist(chat_id, msg_id, callback_id)
        #
        #     else:
        #         error(chat_id)

        # Auf Gruppen-Buttons reagieren
        if menue == "Gruppen":

            for tag in data["chats"]:
                if button == "chat" + tag:
                    bot.answerCallbackQuery(callback_id)

                    users[str(chat_id)]["menue"] = "Gruppen/Senden"
                    users[str(chat_id)]["forward_to"] = data["chats"][tag][0]
                    save("Daten/users.json", users)

                    bot.sendMessage(chat_id, "Bitte sende mir deine Nachricht, dann leite ich sie an " + data["chats"][tag][1] + " weiter...", reply_markup=build_remove_menu())

            if button == "springer":
                users[str(chat_id)]["modus"] = MO_SPRINGER
                save("Daten/users.json", users)

                aktuelle_springer = ""
                for id in users:
                    if users[id]["is_springer"]:
                        aktuelle_springer += users[id]["name"] + ", "
                aktuelle_springer = aktuelle_springer[:-2]

                bot.sendMessage(chat_id, "Schick mir bitte deine Nachricht, dann leite ich sie weiter an " + aktuelle_springer, reply_markup=build_remove_menu())

            # elif button == "all":
            #     all(chat_id, msg_id, msg["from"]["id"])

        # TODO: data["info"] einfacher speichern
        # Auf Info-Anzeigen-Buttons reagieren
        elif menue == "Info":
            # Wenn Info zu Button, dann anzeigen. Wenn nicht (alter Button wurde geklickt, oder sie wurde schon gelöscht), Fehlermeldung
            if button in data["infos"]:
                users[str(chat_id)]["menue"] = "Info/Anzeigen"
                save("Daten/users.json", users)

                bot.answerCallbackQuery(callback_id)
                bot.sendMessage(chat_id, "Unter _" + button + "_ habe ich folgendes gespeichert:", parse_mode="Markdown")
                bot.sendMessage(chat_id, data["infos"][button][1], reply_markup=build_keyboard_menu(const.menu_back_main))
            else:
                bot.answerCallbackQuery(callback_id)
                bot.sendMessage(chat_id, "Es gibt keine Information namens _" +  button + "_. Tippe auf Zeilen, um Informationen zu erhalten.", parse_mode="Markdown", reply_markup=build_button_menu(data["infos"]))

        elif menue == "Info/Entfernen":
            # Wenn Info zu Button, dann löschen und bearbeiten. Wenn nicht (alter Button wurde geklickt, oder sie wurde schon gelöscht), Fehlermeldung
            if button in data["infos"]:
                bot.answerCallbackQuery(callback_id)

                del data["infos"][button]
                save("Daten/data.json", data)

                bot.editMessageText((chat_id, users[str(chat_id)]["display_message"]), "Tippe Buttons an, um Informationen zu löschen.", reply_markup=build_button_menu(data["infos"]))
            else:
                bot.answerCallbackQuery(callback_id)
                bot.sendMessage(chat_id, "Es gibt keine Information namens _" +  button + "_. Tippe auf Zeilen, um Informationen zu löschen.", parse_mode="Markdown", reply_markup=build_button_menu(data["infos"]))

        # Auf Info-Löschen-Buttons reagieren
        elif menue[:12] == "info/löschen":
            if deleteinfo(chat_id, msg_id, callback_id, button):
                pass
            else:
                error(chat_id)

        elif menue[:23] == "Einkaufsliste/Entfernen":

            if button == "alleslöschen":
                bot.answerCallbackQuery(callback_id, text="Die Einkaufsliste ist jetzt leer.", show_alert=True)

                data["einkaufsliste"] = []
                save("Daten/data.json", data)
                users[str(chat_id)]["menue"] = "Einkaufsliste"
                save("Daten/users.json", users)

                bot.sendMessage(chat_id, "Auf der Einkaufsliste stehen:", reply_markup=build_keyboard_menu(const.menu_add_remove), parse_mode="Markdown")

            else:
                for item in data["einkaufsliste"].copy():
                    if button == item:
                        data["einkaufsliste"].remove(item)
                        save("Daten/data.json", data)

                        bot.answerCallbackQuery(callback_id, text = item + " wurde von der Einkaufsliste gelöscht. Tippe weitere Artikel an, um sie zu löschen.")

                        bot.editMessageText((chat_id, users[str(chat_id)]["display_message"]), "Tippe Buttons an, um Artikel zu entfernen", reply_markup=build_button_menu(data["einkaufsliste"], const.footer_shoplist_delete))

    else:
        error(chat_id)


    # debugging
    #pp.pprint(msg)
    #pp.pprint(users)


#################################
# ---   TELEPOT STARTEN     --- #
#################################

bot = telepot.Bot(TOKEN)

MessageLoop(bot, handle).run_as_thread()
print("Ich lese mit ...")
while 1:
    time.sleep(10)
