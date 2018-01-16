# -*- coding:utf-8 -*-
import base64
import datetime
import logging
import logging.handlers
import os
import smtplib
import sqlite3
import time
from datetime import datetime
from email import encoders
from email.mime.base import MIMEBase
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.header import Header

import dateutil.parser as parser
import pymysql
from apiclient import discovery
from bs4 import BeautifulSoup
from httplib2 import Http
from oauth2client import file, client, tools


# 기록할 logger를 설정한다.
def set_logger():
    logging.basicConfig(filename='./log/my.log', level=logging.DEBUG)
    logger = logging.getLogger("") #이름
    logger.setLevel(logging.DEBUG)
    fileHandler = logging.FileHandler('./log/my.log')
    streamHandler = logging.StreamHandler()
    formatter = logging.Formatter('[%(levelname)s | %(filename)s : %(lineno)s] %(asctime)s > %(message)s')
    fileHandler.setFormatter(formatter)
    streamHandler.setFormatter(formatter)
    logger.addHandler(fileHandler)
    logger.addHandler(streamHandler)
    return logger

def get_message():
    # Creating a storage.JSON file with authentication details
    SCOPES = 'https://www.googleapis.com/auth/gmail.modify'  # we are using modify and not readonly, as we will be marking the messages Read
    store = file.Storage('storage.json')
    creds = store.get()
    if not creds or creds.invalid:
        flow = client.flow_from_clientsecrets('client_secret.json', SCOPES)
        creds = tools.run_flow(flow, store)
    GMAIL = discovery.build('gmail', 'v1', http=creds.authorize(Http()))

    user_id = 'me'
    label_id_one = 'INBOX'
    label_id_two = 'UNREAD'

    checkSenderList = ["", "", ""] #이메일 보낸사람 리스트
    flag = 'true'
    outputList = []

    # Getting all the unread messages from Inbox
    # labelIds can be changed accordingly
    unread_msgs = GMAIL.users().messages().list(userId='me', labelIds=[label_id_one, label_id_two]).execute()

    # We get a dictonary. Now reading values for the key 'messages'
    try:
        mssg_list = []
        mssg_list = unread_msgs['messages']
    except Exception as err:
        logger.error(err)
        logger.error(mssg_list)
    logger.debug("Total unread messages in inbox: " + str(len(mssg_list)))

    final_list = []

    for mssg in mssg_list:
        flag = 'false'
        temp_dict = {}
        temp_output_dic = {}
        m_id = mssg['id']  # get id of individual message
        message = GMAIL.users().messages().get(userId=user_id, id=m_id).execute()  # fetch the message using API
        payld = message['payload']  # get payload of the message
        headr = payld['headers']  # get header of the payload

        for one in headr:  # getting the Subject
            if one['name'] == 'Subject':
                msg_subject = one['value']
                temp_dict['Subject'] = msg_subject
            else:
                pass

        for two in headr:  # getting the date
            if two['name'] == 'Date':
                msg_date = two['value']
                date_parse = (parser.parse(msg_date))
                m_date = (date_parse.date())
                temp_dict['Date'] = str(m_date)
                temp_output_dic['Date'] = str(m_date)
            else:
                pass

        for three in headr:  # getting the Sender
            if three['name'] == 'From':
                msg_from = three['value']
                temp_dict['Sender'] = msg_from
                temp_output_dic['Sender'] = msg_from
                # print("발신자 : " + msg_from)
                for check in checkSenderList:
                    if temp_dict['Sender'].find(check) > 0:
                        flag = 'true'
                        break
            else:
                pass

        temp_dict['Snippet'] = message['snippet']  # fetching message snippet

        if flag == 'true':
            try:
                # Fetching message body
                # print(payld)
                mssg_parts = []
                mssg_parts = payld['parts']  # fetching the message parts
                part_one = mssg_parts[0]  # fetching first element of the part
                part_body = part_one['body']  # fetching body of the message
                part_data = part_body['data']  # fetching data from the body
                clean_one = part_data.replace("-", "+")  # decoding from Base64 to UTF-8
                clean_one = clean_one.replace("_", "/")  # decoding from Base64 to UTF-8
                clean_two = base64.b64decode(bytes(clean_one, 'UTF-8'))  # decoding from Base64 to UTF-8
                soup = BeautifulSoup(clean_two, "lxml")
                # print(soup)
                mssg_body = soup.body()
                # mssg_body is a readible form of message body
                # depending on the end user's requirements, it can be further cleaned
                # using regex, beautiful soup, or any other method
                temp_dict['Message_body'] = mssg_body
            except Exception as ss:  # 에러 종류
                logger.error(str(ss))
                pass

            # print (temp_dict)
            raw = str(temp_dict['Message_body'])
            pro_num = ""
            order_num = ""
            pro_name = ""
            pro_mon = ""
            pro_qu = ""
            if raw.find("옥션") > 0:
                numPronum = raw.find('상품번호/주문번호')  # 9글자
                numProname = raw.find("상품명")  # 3글자
                product_num_and_orderNum = raw[numPronum + 9:numProname]
                product_num_and_orderNum = product_num_and_orderNum.replace('\n', '')
                product_num_and_orderNum = product_num_and_orderNum.strip()
                # print("상품번호/주문번호 : " + product_num_and_orderNum)
                pro_num = product_num_and_orderNum[0:product_num_and_orderNum.find('(')]
                order_num = product_num_and_orderNum[
                            product_num_and_orderNum.find('(') + 1:product_num_and_orderNum.find(')')]
                # print("상품번호 : " + pro_num)
                # print("주문번호 : " + order_num)
                numSellMoney = raw.find('판매금액(수량)')  # 8글자
                pro_name = raw[numProname + 3:numSellMoney]
                pro_name = pro_name.replace('\n', '')
                pro_name = pro_name.strip()
                # print("상품명 : " + pro_name)

                numMon_qu = raw.find('결제일자')  # 4글자
                numMon_qu = raw[numSellMoney + 8:numMon_qu]
                numMon_qu = numMon_qu.replace('\n', '')
                numMon_qu = numMon_qu.strip()
                # print("판매금액(수량) : " + numMon_qu)
                pro_mon = numMon_qu[0:numMon_qu.find('(')]
                pro_mon = pro_mon.replace("원", "")
                pro_qu = numMon_qu[numMon_qu.find('(') + 1:numMon_qu.find(')')]
                pro_qu = pro_qu.replace("개", "")
                # print("판매금액 : " + pro_mon)
                # print("수량 : " + pro_qu)
                temp_output_dic['Product_Number'] = pro_num
                temp_output_dic['Order_Number'] = order_num
                temp_output_dic['Product_Name'] = pro_name
                temp_output_dic['Money'] = pro_mon
                temp_output_dic['Quantity'] = pro_qu
                outputList.append(temp_output_dic)
            # print(temp_output_dic)

            final_list.append(temp_dict)  # This will create a dictonary item in the final list

    # This will mark the messagea as read
    # GMAIL.users().messages().modify(userId=user_id, id=m_id,body={ 'removeLabelIds': ['UNREAD']}).execute()

    # logger.debug("Total messaged retrived: ", str(len(final_list)))
    return outputList

def insert_table(data):
    try:
        conn = pymysql.connect(host='', port=, user='', password='', database='', charset = "utf8")
        # conn = sqlite3.connect("./myDB.db")
        cur = conn.cursor()
        logger.debug(data['Sender'])
        logger.debug(data['Product_Number'])
        logger.debug(datetime)

        sql = "INSERT INTO output (sender,pro_num, order_num, pro_name, date, money, quantity) VALUES (%s,%s,%s,%s,%s,%s,%s);"
        cur.execute(sql, (data['Sender'],data['Product_Number'],data['Order_Number'],data['Product_Name'],"20171221",data['Money'],data['Quantity']))
        # cur.execute(sql, (sender, pro_num, order_num, pro_name, datetime, money,quantity))

        conn.commit()
        # 만약 mysql 부분에서 문제가 발생시 sqlite에 임의로 저장.
    except Exception as ex:
        logger.error(ex)
        # print(ex.with_traceback())
        try:
            sq_con = sqlite3.connect("./myDB.db")
            sql = "INSERT INTO output (sender,pro_num, order_num, pro_name, date, money, quantity) VALUES (?,?,?,?,?,?,?);"
            sq_con.execute(sql, (data['Sender'], data['Product_Number'], data['Order_Number'], data['Product_Name'], "20171221", data['Money'],data['Quantity']))
            sq_con.commit()
            logger.error("문제가 발생하여 임시로 myDB.db(sqlite3)에 저장합니다.")
            logger.error("저장한 내용 : " + str(data))
        except Exception as s:
            logger.error(s)
    finally:
        conn.close()
        logger.debug("Insert Query Complete")

def get_code(Codetype):
    returnCode = list()
    logger.debug("Codetype : " +Codetype)
    try:
        conn = pymysql.connect(host='', port=, user='', password='', database='', charset = "utf8")
        # conn = sqlite3.connect("./myDB.db")
        cur = conn.cursor()
        if Codetype == "55555":
            logger.debug("In get_code(), codeType == 55555")
            sql = "SELECT min(seq), type, code, num from codeBook where type = %s;"
        else:
            logger.debug("In get_code(), codeType != 55555")
            sql = "SELECT min(seq), type, code from codeBook where type = %s;"
        cur.execute(sql,(Codetype,))
        rows = cur.fetchall()
        for a in rows:
            for k in range(len(a)):
                logger.debug("k : "+ str(k) + "   " + str(a[k]))
                returnCode.append(a[k])
            logger.debug("code : " + a[2])
        logger.debug("returnCode")
        logger.debug(returnCode)
        # 가져온 코드의 타입이 5번이면 count 값이 4이면 삭제 아니면 count를 1 증가시킨다.
        if Codetype == "55555":
            if int(returnCode[3]) == 4:
                logger.debug("In get_code(), int(code[3]) == 4")
                sql = "delete from codeBook where seq = %s;"
                cur.execute(sql, (a[0],))
                conn.commit()
            else:
                logger.debug("In get_code(), int(code[3]) != 4")
                cnt = returnCode[3]
                cnt = cnt + 1
                sql = "update codeBook SET  num = %s where seq = %s;"
                logger.debug("cnt : " + str(cnt) + "  seq : " + str(a[0]))
                cur.execute(sql, (cnt, a[0]))
                conn.commit()
        else:
            sql = "delete from codeBook where seq = %s;"
            cur.execute(sql, (a[0],))
            conn.commit()
    except Exception as ss:  # 에러 종류
        logger.error(str(ss))
    finally:
        conn.close()
        logger.debug("Complete get_code()")

    return returnCode

# execute 부분에 지금은 일일히 손으로 다 코드를 박아줬지만 메일에서 추출한 값을 수정한 후에는 여기에 변수로 바꿔넣어야함.
# count랑 orderNum이 추가되었으므로 Query에 넣어줘야함.
# code[0] => seq, code[1] => type, code[2] => code, (코드 타입이 5번일떄만!!) code[3] => count
def insertUsedCode(type, code, buyerName, buyerEmail, shoppingMall, price, order_num):
    conn = pymysql.connect(host='', port=, user='', password='', database='', charset = "utf8")
    # conn = sqlite3.connect("./myDB.db")
    cur = conn.cursor()

    #code[0] => seq, code[1] => type, code[2] => code
    try:
        now = time.strftime('%Y-%m-%d %H:%M:%S')
        if str(code[1]) == "55555":
            logger.debug("IN inserUsedCode, in code[1] == 55555")
            logger.debug(code[1])
            num = int(code[3])
            num = num + 1
            # 이미 get_code에서는 num을 증가시켰지만 여기서의 code[3]는 insert하기 전의 값이므로 이해하기 쉽게하기 위해 1을 더해준다.
            sql = "INSERT INTO UsedCode(type, code, UsedDate, buyerName, buyerEmail, shoppingMall, price, num, order_num) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s);"
            cur.execute(sql, (type, code[2], now, buyerName, buyerEmail, shoppingMall, price, num, order_num))
        else:
            logger.debug("IN inserUsedCode,  code[1] != 55555")
            logger.debug(code[1])
            sql = "INSERT INTO UsedCode(type, code, UsedDate, buyerName, buyerEmail, shoppingMall, price, order_num) VALUES (%s,%s,%s,%s,%s,%s,%s,%s);"
            cur.execute(sql, (type, code[2], now, buyerName, buyerEmail, shoppingMall, price, order_num))
        conn.commit()
    except Exception as ss:  # 에러 종류
        logger.error(ss)
        # 에러가 나서 프로그램이 뻗더라도 어떤 코드를 쓰고 뻗었는지 기록.
        # output_list = list()
        # temp_dict ={}
        # temp_dict['type'] = type
        # if code[2] == None:
        #     temp_dict['code'] = "noCode"
        # else:
        #     temp_dict['code'] = code[2]
        # temp_dict['UsedDate'] = "2017-12-21"
        # print(now)
        # temp_dict['buyerName'] = buyerName
        # temp_dict['buyerEmail'] = buyerEmail
        # temp_dict['shoppingMall'] = shoppingMall
        # price = str(price).replace(",","")
        # temp_dict['price'] = price
        # output_list.append(temp_dict)
        # print(output_list)
        # with open('output.csv', 'a', encoding='ANSI', newline='') as csvfile:
        #     fieldnames = ['type','code','UsedDate','buyerName','buyerEmail','shoppingMall','price']
        #     writer = csv.DictWriter(csvfile, fieldnames=fieldnames, delimitesr=',')
        #     writer.writeheader()
        #     for val in output_list:
        #     	writer.writerow(val)

    finally:
        conn.close()
        logger.debug("Complete insertUsedCode()")

#Create Module
def mail(to, subject, text, attach):
   msg = MIMEMultipart()
   msg['From'] = gmail_user
   msg['To'] = ", ".join(recipients)
   # msg['Subject'] = subject
   msg['Subject'] = Header(subject,'utf-8')
   msg.attach(MIMEText(text, 'plain', 'utf-8'))  # 내용 인코딩
   # msg.attach(MIMEText(text))

   #get all the attachments
   for file in filenames:
        part = MIMEBase('application', 'octet-stream')
        part.set_payload(open(file, 'rb').read())
        encoders.encode_base64(part)
        # part.add_header('Content-Disposition', 'attachment; filename=%s' %file)
        # part.add_header('Content-Disposition', 'attachment; filename=%s' %os.path.basename(file))
        part.add_header('Content-Disposition', 'attachment', filename=('utf-8', '', str(os.path.basename(file))))
        logger.debug("file!!")
        logger.debug(file)
        msg.attach(part)

   mailServer = smtplib.SMTP("smtp.gmail.com", 587)
   mailServer.ehlo()
   mailServer.starttls()
   mailServer.ehlo()
   mailServer.login(gmail_user, gmail_pwd)
   mailServer.sendmail(gmail_user, to, msg.as_string())
   # Should be mailServer.quit(), but that crashes...
   mailServer.close()

if__name__ = '__main__';

# logger Setting , Get DB Connection Object
logger = set_logger()


# GMail로 부터 메일을 가져와서 필요한 정보를 추출하여 output_list에 저장.
output_list = get_message()
# 추출한 정보를 확인하고 확인된 정보는 output 테이블에 저장.
for a in range(len(output_list)):
    logger.debug(output_list.__getitem__(a))
    insert_table(output_list.__getitem__(a))

# 주문이 들어왔으니 코드를 꺼내서 주문자에게 다시 보내줘야함.
# !! 여기서는 pro_num(상품번호)를 '코드타입'으로 정한다. => 추후에 테이블 자체가 바뀔 수 있음.
# !1 database is locked라는 에러가 발생함.. dbBrowser를 끄면 잘 작동하는데.. mysql로 바꿔야하나 검토
for a in range(len(output_list)):
    logger.debug("주문한 수량 : "+output_list.__getitem__(a)['Quantity'])
    # 주문한 수량 만큼 코드를 가져온다.
    qu = output_list.__getitem__(a)['Quantity']
    #일단 가라로 다 만든다음 나중에 제대로된 예제가 있으면 수정.
    codeType = output_list.__getitem__(a)['Product_Number']
    order_num = output_list.__getitem__(a)['Order_Number']
    price = output_list.__getitem__(a)['Money']
    name = "" # 이름
    email = "" # 이메일
    sender = output_list.__getitem__(a)['Sender']
    mall = sender[sender.find('<')+1:sender.find('>')]

    # code = get_code(codeType) <- 아직 product_number가 진짜 판매되는 상품코드가 아니라 일단은 밑에 코드로.
    # code[0] => seq, code[1] => type, code[2] => code, code[3] => count(코드 타입이 5번일떄만!!)
    codeList = [] # 수량대로 코드를 불러온 코드를 저장하고 나중에 메일로 전송할 떄 이 코드리스트에서 저장한 코드를 사용함.
    for k in range(int(qu)):
        code = get_code("55555")
        # 만약 가져와야할 코드의 타입의 5번이면 count를 가져와야함. = > count는 code[3]에 정보가 들어있다.
        #사용된 코드를 UsedCode 테이블에 기록한다.
        insertUsedCode(codeType, code, name, email, mall, price, order_num)

    #Set up crap for the attachments
    files = "./attachFile"
    filenames = [os.path.join(files, f) for f in os.listdir(files)]
    logger.debug("filenames!!")
    logger.debug(filenames)
    #print filenames
    #Set up users for email
    gmail_user = ""
    gmail_pwd = ""
    recipients = ['@naver.com','@naver.com']
    mail(recipients,"저희 가게를 이용해주셔서 감사합니다.", "감사합니다.",filenames)

logger.debug("End")


#gmail_user, gmail_pwd
#host, password, user, etc..
#email(recipients)