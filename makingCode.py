import pymysql
import random
import logging
import time

def code_generator(howMany):
    finalList = []
    for k in range(howMany):
        alpabet = ['A','B','C','D','E','F','G','H','I','J','K','L','N','M','O','P','Q','R','S','T','U','V','W','X','Y','Z']
        codeType = ["11111", "22222", "33333", "44444", "55555"]
        codeList = {}
        random.shuffle(alpabet)
        code = ""
        for a in range(25):
            a = a+1
            code = code + alpabet[a]
            if (a%5 == 0) & (a != 25):
                code = code + "-"
        type = random.choice(codeType)
        logger.debug("Created Code : " + code +"  Type : " + type)
        codeList['code'] = str(code)
        codeList['type'] = str(type)
        finalList.append(codeList)
    return finalList
def set_logger():
    logging.basicConfig(filename='./log/my.log', level=logging.DEBUG)
    logger = logging.getLogger("JiYul")
    logger.setLevel(logging.DEBUG)
    fileHandler = logging.FileHandler('./log/my.log')
    streamHandler = logging.StreamHandler()
    formatter = logging.Formatter('[%(levelname)s | %(filename)s : %(lineno)s] %(asctime)s > %(message)s')
    fileHandler.setFormatter(formatter)
    streamHandler.setFormatter(formatter)
    logger.addHandler(fileHandler)
    logger.addHandler(streamHandler)
    return logger
def insertCode(codeBook):
    try:
        conn = pymysql.connect(host='115.71.232.235', port=3306, user='root', password='',
                               database='EmailReader', charset="utf8")
        # conn = sqlite3.connect("./myDB.db")
        cur = conn.cursor()
        for val in codeBook:
            now = time.strftime('%Y-%m-%d %H:%M:%S')

            if val['type'] == "55555":
                sql = "INSERT INTO codeBook (type, code, createdDate, num) VALUES (%s,%s,%s,%s);"
                cur.execute(sql, (val['type'], val['code'], now, int(0)))
            else:
                sql = "INSERT INTO codeBook (type, code, createdDate) VALUES (%s,%s,%s);"
                cur.execute(sql, (val['type'], val['code'], now))

            conn.commit()
            logger.debug("Code Insert Complete : "  + str(val))
    except Exception as ex:
        logger.error(ex)
        print(ex.with_traceback())
    finally:
        conn.close()
        logger.debug("Insert Query Complete")


if__name__ = '__main__';
logger = set_logger()
# 코드를 무작위로 만들어낸다.
codeBook = code_generator(200)
# 데이터베이스에 코드를 기록.
insertCode(codeBook)
