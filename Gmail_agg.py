
from doctest import debug
import imaplib, email
import config as cfg
import time
import sys
import keyboard
from imapclient import IMAPClient
from datetime import datetime
import socket, ssl


#-------------------------------INIT----------------------------------------

user        = cfg.my_mail_config["user"]
password    = cfg.my_mail_config["password"]
imap_url  = "imap.gmail.com"
mailbox="Inbox"
#tls_context = ssl.create_default_context()


#-------------------------------Definice jednotlivých fcí --------------------


def login(mailbox):
    """Login func to the email client using SSL and imaplib
    Args:
        mailbox (str): which section/category of the mail client should be selected i.e. "Inbox", "Spam" or "Sent"
    Returns:
        mail: imap4_SSL connection and port variable
        status: Con status
        messages: Messages within selected category
    """
    #print('Logging in again')
    mail = imaplib.IMAP4_SSL(imap_url,993)
    mail.debug = True
    mail.login(user,password)
    status, messages = mail.select(mailbox, readonly= True)
    time.sleep(1)
    return mail, status, messages

def login_w_imapclient():
    """Login function using IMAPCleint instead. Used for .Idle function
    Returns:
        server: IMAPClient
    """
    server = IMAPClient(imap_url)
    server.login(user,password)
    server.select_folder("Inbox", readonly=True)
    time.sleep(1)
    return server

#odstraňuje ze sizu contractu nechtěné symboly
def remove_hidden_chars(string):
    """Removing hidden chars from mail formatting.
    Args:
        string (str): string you want to remove chars from
    Returns:
        string: cleaned string from the hidden chars
    """
    try:
        string = float(string.replace("\r\n}", ""))
        return string

    except Exception as chyba:
        if chyba:
            print(chyba)
            return 0.0



def Idle_seq (gem):
    """set the function to Idle state for 600 seconds by default, then reseting the idle state. Code awaits signal. Once received it passes the signal to the engine

    Args:
        gem (int): 0/1 value used for checking the state of the connection. gem is passing it´s value to signal awaiter system

    Returns:
        gem: _description_
        byloEOF: check whener there was EOF error, so it will re-initialize the code from the engine
    """
    server = login_w_imapclient()
    server.idle()
    print(datetime.now())
    print("Connection is now in IDLE mode, send yourself an email or quit with alt+p")
    starting_time = time.time()
    elapsed_time = 0 #je zde kvůli tomu, že ten Idle se musí cca za 10 minut shodit a pak zase nahodit, jinak to serveru vadí
    while True:
        elapsed_time = time.time()-starting_time
        if keyboard.is_pressed('alt+p'):  # if key 'q' is pressed 
            print('Vyskakuji manuálně z Idlu')
            break  # finishing the loop
        try:
            # Wait for up to 1 seconds for an IDLE response
            responses = server.idle_check(timeout=1)
            #print("Server sent:", responses if responses else "nothing")            #pokud chci print odezvy
            if responses:
                print("Server sent:", responses)
                gem = 1
                byloEOF = 0
                server.idle_done()
                server.logout()
                print("\nIDLE mode done, New mail found")
                return gem, byloEOF
            elif elapsed_time > 600:
                gem = 0
                byloEOF = 0
                server.idle_done() 
                server.logout()      
                print("\nIDLE mode done, Time out")
                return gem, byloEOF
        except Exception or OSError or EOFError as chyba:
            exception_type, exception_object,exception_traceback = sys.exc_info() #exception_type, exception_object, 
            #filename = exception_traceback.tb_frame.f_code.co_filename
            line_number = exception_traceback.tb_lineno
            print(exception_type)
            print(exception_object)
            print("problém se vyskytl v Idlu")
            print (chyba)
            print("Line number", line_number)
            gem = 0
            byloEOF = 1
            return gem, byloEOF   




#===================================== Funkce returning actual mail sliced ===============================================================================

#vrací nejaktuálnější mail, v kterém pak rozkrájím na slova, jenž pak použiji pro jednotlivé signály

def get_alert(Mail_number):
    """Using login function establish connection with the email client. Select the latest mail, convert it from bytes
    and get it´s body. From the body get the sentence which is splitted into words and reflect outgoing steps for bot, get rid of 
    hidden chars and pass these variables out.
    
    Args:
        Mail_number(int): number of the mail we want to get. starting from 1 as the newest

    Returns:
        to_do: what action to take i.e. ENTER-LONG or EXIT-SHORT
        market: on which market pair to take this action (SOL-USDC)
        contract_size: size of the order
        bylo_EOF: failsafe if there was a EOF error
    """
    mail,status,messages = login("Inbox")
    messages = int(messages[0])
    counter = 0
    for i in range (messages,messages - Mail_number, -1):
        res, msg = mail.fetch(str(i), "(RFC822)")
        for response in msg:
            if isinstance(response,tuple):
                msg = email.message_from_bytes (response[1])
                #datem ="Date:" + msg["Date"]            pokud bych si chtěl printnout datum
                body = msg.get_payload()
                try:
                    if body.find("qty") > 0 and counter == 0:
                        slova = body.split(" ") # rozdělí body content na jednotlivá slova kde je rozdělovačem SPACE
                        """
                        print(slova[6]) 
                        print(slova[7])
                        print(slova[13])
                        """
                        to_do = str(slova[6]) # Akce k provedení
                        market = slova[7] #Market trh na kterém má bot obchodovat
                        contract_size = slova[13] #velikost pozice nominovaná v kontraktu
                        contract_size = remove_hidden_chars(contract_size)
                        print(str(to_do)+(" ")+str(market)+(" ")+str(contract_size))
                        
                        counter = 1
                        bylo_eof = 0
                        print(mail.close())
                        print(mail.logout())
                        return to_do, market, contract_size, bylo_eof 
                    else:
                        to_do = "nothing"
                        market = "none"
                        contract_size = "0"
                        print(mail.close())
                        print(mail.logout())
                        bylo_eof = 0
                        return to_do, market, contract_size, bylo_eof 
                except Exception or OSError or EOFError as chyba:
                    exception_type, exception_object,exception_traceback = sys.exc_info() #exception_type, exception_object, 
                    #filename = exception_traceback.tb_frame.f_code.co_filename
                    line_number = exception_traceback.tb_lineno
                    print(exception_type)
                    print(exception_object)
                    print("problém se vyskytl v get Alertu")
                    print (chyba)
                    print("Line number", line_number)
                    time.sleep(10)
                    print("spal jsem 10 sekund")
                    bylo_eof = 1
                    return to_do, market, contract_size, bylo_eof     
to_do, market, contract_size, bylo_eof = get_alert(1)

#===================================== Funkce search for signal ===============================================================================

# motor čtení z mailu. neloguje se hned, ale až v jednotlivých krocích. Idle_seq se loguje přes IMAPclietna a get_alert přes klasický IMAP4.SSL
def signal_awaiter_system():
    """Main func for Mail aggregator system which is using func within. Such as Idle_seq or get_alert.
    afterwards aggregate instructions for main bot engine which will execute orders.

    Returns:
        to_do: what action to take i.e. ENTER-LONG or EXIT-SHORT
        market: on which market pair to take this action (SOL-USDC)
        contract_size: size of the order
        bylo_EOF: failsafe if there was a EOF error
    """
    gem = 0
    bylo_EOF = 0
    while True: 
        try:
            if gem == 0 and bylo_EOF == 0:
                gem, bylo_EOF = Idle_seq(gem) # gem je zde jako zadaná i vrácená hodnota
                print("gem je: " + str(gem))
            elif gem == 1 and bylo_EOF == 0:
                to_do,market, contract_size, bylo_EOF =  get_alert(1)
                print("alerty by se měly rozeslat")
                return to_do,market, contract_size, bylo_EOF
            elif bylo_EOF == 1:
                print("bylo EOF, spím na 30 sec")
                time.sleep(30)
                gem, bylo_EOF = Idle_seq(gem)
                print("gem je: " + str(gem))

            elif keyboard.is_pressed('alt+p'):  # if key 'ctrl+q' is pressed 
                print('Vyskakuji manuálně do main menu')
                break  # finishing the loop
            
        except Exception or OSError or EOFError as chyba:
            exception_type, exception_object,exception_traceback = sys.exc_info() #exception_type, exception_object, 
            #filename = exception_traceback.tb_frame.f_code.co_filename
            line_number = exception_traceback.tb_lineno
            print(exception_type)
            print(exception_object)
            print("problém se vyskytl v samotném Awaiteru")
            print (chyba)
            print("Line number", line_number)
            break 





#===================================== OLD DATA ==============================================================
#Tento awaiter je pro seznam maily
"""
def signal_awaiter_system():
    mail = login("Inbox")
    latest_email_uid = ''
    second_latest_uid = ""
    first_skip = 0 # je nutný, protože poprvé co code protéká, tak second_latest_uid se také liší od toho latest
    print_counter = 0
    while True:
        result, data = imap.uid('search', None, "ALL") # search and return uids instead  
        #result, data = imap.search()
        ids = codecs.decode(data[0],"UTF-8") # data is a list.
        latest_email_uid = int(ids.split()[-1])
        time.sleep(0.1)
        try:            
            if latest_email_uid != second_latest_uid and first_skip == 0:
                first_skip = 1
                print("Init jsem přeskočil")
            elif latest_email_uid != second_latest_uid and first_skip == 1:
                    alert = get_alert()
                    to_do,market, contract_size, datem = alert
                    print("alerty by se měly rozeslat")
                    return to_do,market, contract_size
                   
            if OSError:
                print(ssl.CertificateError(mail))
                del(mail)
                time.sleep(3)
                mail = login("Inbox")
                print(datetime.now())
                print("Byl socket error, del a relognuto")   
                
        except Exception as chyba:
            exception_type, exception_object,exception_traceback = sys.exc_info() #exception_type, exception_object, 
            #filename = exception_traceback.tb_frame.f_code.co_filename
            line_number = exception_traceback.tb_lineno
            mail = login("Inbox")
            print (chyba)
            print("Line number", line_number)  
        second_latest_uid = int(ids.split()[-1])
        print_counter +=1
        if print_counter == 5:
            print("Vyhlížím signál")   
        elif print_counter == 150:
            print("Stále Vyhlížím signál")
        elif print_counter == 444:
                print("Už nebudu tolik spamovat, ale stále vyhlížím signál ")
        elif keyboard.is_pressed('q'):  # if key 'q' is pressed 
            print('Vyskakuji manuálně do main menu')
            break  # finishing the loop
    print(mail.close())
    print(mail.logout()) 
    """ 
        
       



# užitečné odkazy
"""
https://web.archive.org/web/20090814230913/http://blog.hokkertjes.nl/2009/03/11/python-imap-idle-with-imaplib2/

ještě to můžu tahat přes NOOP command
https://stackoverflow.com/questions/49695529/python-imap-search-not-updated
"""



















             
# Z tohoto si možná něco můžu případně vypitvat

"""
Nechal jsem si tento kod pro jeho eleganci, ale nefungoval :D
def remove_hidden_chars(string,n):
    try:
        string.strip()
        string = "".join(c for c in string if c.isprintable())
        string = string[0:n]
        #print(len(string))
        print("kod tudy protekl")
        return string
    except Exception as chyba:
        if chyba:
            print(chyba)
            return remove_hidden_chars(string,n-1)
"""


"""
with imap.login as mailbox:
    for message in mailbox.fetch(limit=1, reverse=True):
        print(message.date_str, message.subject,)

# we'll search using the ALL criteria to retrieve
# every message inside the inbox
# it will return with its status and a list of ids
status, data = mail.search(None, 'ALL')
# the list returned is a list of bytes separated
# by white spaces on this format: [b'1 2 3', b'4 5 6']
# so, to separate it first we create an empty list
mail_ids = []
# then we go through the list splitting its blocks
# of bytes and appending to the mail_ids list
for block in data:
    # the split function called without parameter
    # transforms the text or bytes into a list using
    # as separator the white spaces:
    # b'1 2 3'.split() => [b'1', b'2', b'3']
    mail_ids += block.split()

# now for every id we'll fetch the email
# to extract its content
for i in mail_ids:
    # the fetch function fetch the email given its id
    # and format that you want the message to be
    status, data = mail.fetch(i, '(RFC822)')

    # the content data at the '(RFC822)' format comes on
    # a list with a tuple with header, content, and the closing
    # byte b')'
    for response_part in data:
        # so if its a tuple...
        if isinstance(response_part, tuple):
            # we go for the content at its second element
            # skipping the header at the first and the closing
            # at the third
            message = email.message_from_bytes(response_part[1])

            # with the content we can extract the info about
            # who sent the message and its subject
            mail_from = message['from']
            mail_subject = message['subject']

            # then for the text we have a little more work to do
            # because it can be in plain text or multipart
            # if its not plain text we need to separate the message
            # from its annexes to get the text
            if message.is_multipart():
                mail_content = ''

                # on multipart we have the text message and
                # another things like annex, and html version
                # of the message, in that case we loop through
                # the email payload
                for part in message.get_payload():
                    # if the content type is text/plain
                    # we extract it
                    if part.get_content_type() == 'text/plain':
                        mail_content += part.get_payload()
            else:
                # if the message isn't multipart, just extract it
                mail_content = message.get_payload()

            # and then let's show its result
            print(f'From: {mail_from}')
            print(f'Subject: {mail_subject}')
            print(f'Content: {mail_content}')
"""