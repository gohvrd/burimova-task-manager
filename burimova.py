import requests
import re
import datetime
import logging
import sys
from bs4 import BeautifulSoup

logging.basicConfig(level=logging.INFO)

s = requests.Session()

tasks_to_check = {}

def string_dictionary_with_arrays(dictionary):
    dict_string = "<html><head><meta charset=\"utf-8\"><title>Задания для проверки</title></head><body><h1>Задания для проверки</h1>"
    for key in dictionary.keys():
        dict_string += f"<h2>{key}</h2>\n"

        for value in dictionary[key]:
            dict_string += f"<p><a href=\"{value}\">\t{value}</a></p>\n"

    return f"{dict_string}</body></html>"

def add_to_dictionary_with_arrays(dictionary, key, value):
    if key in dictionary.keys():
        dictionary[key].append(value)
    else:
        dictionary[key] = [value]

def authorization(login, password):
    proxies = {'http': 'localhost:8080','https': 'localhost:8080'}
    
    login_form_request = s.get("https://school.burimova.ru/cms/system/login")

    if login_form_request:
        csrfToken_pat = re.compile(r"window\.csrfToken = \"([a-zA-Z0-9\=]+)\"")
        gcUniqId_pat = re.compile(r"window\.gcUniqId = \"([a-z0-9\.]+)\"")
        simpleSign_pat = re.compile(r"window\.requestSimpleSign = \"([a-z0-9]+)\"")

        csrfToken_find = re.search(csrfToken_pat, login_form_request.text)
        gcUniqId_find = re.search(gcUniqId_pat, login_form_request.text)
        simpleSign_find = re.search(simpleSign_pat, login_form_request.text)

        if csrfToken_find is not None and gcUniqId_find is not None and simpleSign_find is not None:
            csrfToken = csrfToken_find.group(1)
            logging.debug(f"csrfToken: {csrfToken}")
            gcUniqId = gcUniqId_find.group(1)
            logging.debug(f"gcUniqId: {gcUniqId}")
            simpleSign = simpleSign_find.group(1)
            logging.debug(f"simpleSign: {simpleSign}")

            currentDate = datetime.datetime.today().strftime("%Y-%d-%m %H:%M")
            logging.debug(f"currentDate: {currentDate}") 

            logging.debug(f"Get url: https://school.burimova.ru/stat/counter?ref=&loc=https://school.burimova.ru/cms/system/login&objectId=-1&uniqId={gcUniqId}&token={csrfToken}&tzof={currentDate}")
            logging.debug(f"request cookie: {s.cookies}")
            r1 = s.get(f"https://school.burimova.ru/stat/counter?ref=&loc=https://school.burimova.ru/cms/system/login&objectId=-1&uniqId={gcUniqId}&token={csrfToken}&tzof={currentDate}")
            
            if r1:               
                logging.debug(f"response status code: {r1.status_code}")
                logging.debug(f"response header: {r1.headers}")

                requestTime = str(datetime.datetime.today().timestamp()).split('.')[0]

                post_data = {'action': 'processXdget', 'xdgetId': '99945', 'params[action]': 'login', 'params[url]': 'https://school.burimova.ru/cms/system/login', 'params[email]': f'{login}', 'params[password]': f'{password}', 'params[null]': '', 'params[object_type]': 'cms_page', 'params[object_id]': '-1', 'requestTime': '1620069281', 'requestSimpleSign': f'{simpleSign}'}
                post_headers = {'User-Agent':'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:88.0) Gecko/20100101 Firefox/88.0',
                'Accept':'*/*',
                'Accept-Language':'en-US,en;q=0.5',
                'Accept-Encoding':'gzip, deflate, br',
                'Content-Type':'application/x-www-form-urlencoded; charset=UTF-8',
                'X-Requested-With':'XMLHttpRequest',
                'Origin':'https://school.burimova.ru',
                'Connection':'close',
                'Referer':'https://school.burimova.ru/cms/system/login',
                'TE':'Trailers'}
                

                logging.debug(f"Post url: https://school.burimova.ru/cms/system/login")
                logging.debug(f"request cookie: {s.cookies}")
                request = requests.Request('POST', "https://school.burimova.ru/cms/system/login", data=post_data, headers=post_headers, cookies=s.cookies)
                prepared_request = request.prepare()
                
                r2 = s.send(prepared_request)

                if r2:
                    response_text = r2.text

                    logging.debug(f"response status code: {r2.status_code}")
                    logging.debug(f"response header: {r2.headers}")
                    logging.debug(f"response text: {response_text}")                   
                    logging.debug(f"current session cookie: {s.cookies}")                    

                    is_errorMessage_search = re.search(re.compile("\"errorMessage\":\"([^\"]+)\""), response_text)

                    if is_errorMessage_search is not None:
                        is_errorMessage = is_errorMessage_search.group(1)
                        #logging.error(f"Authorization error: {bytes(is_errorMessage).decode('utf-8')}")
                        logging.error(f"Authorization error: Неверный логин или пароль")
                        input("Press any key to exit")
                        exit(1)
                    else:                        
                        is_success_search = re.search(re.compile("\"success\":([a-z]+),"), response_text)

                        if is_success_search is not None:
                            is_success = is_success_search.group(1)
                        else:
                            logging.error("bad response")
                            input("Press any key to exit")
                            exit(1)
                        if is_success == 'false':
                            logging.error("Authorization unexpected error")
                            input("Press any key to exit")
                            exit(1)
                        elif is_success == 'true':
                            logging.info("Authorization completed!")
                        else:
                            logging.error("bad response status")
                            input("Press any key to exit")
                            exit(1)
        else:
            logging.error("Authorization unexpected error")
            input("Press any key to exit")
            exit(1)
            
def find_unmarked_tasks(url, filename):
    response = s.get(url)
    pattern=re.compile("Задание[\s]*ожидает[\s]*проверки")
    result = re.findall(pattern, response.text)
    
    if len(result) != 0:
        fw = open(filename, "a")
        fw.write(url+"\n")
        fw.close()

def get_creds(filename):
    try:
        fr_login = open(filename, "r")
    except:
        logging.error(f"file \"{filename}\" not found")
        exit(1)

    creds = fr_login.read().strip()

    if re.match(re.compile(r"^[\w@\.\-\_]+::[^$]+$"), creds) is not None:
        (login, password) = creds.split('::')

        return login, password
    else:
        logging.error(f"{filename} - wrong format")

        return None

def task_finder(url):
    response = s.get(url)
    
    if response.status_code == 200 and len(response.text) != 0:
        page = BeautifulSoup(response.text, 'lxml')

        answers = page.find("div", {"class":"answers-list"})

        if answers is not None:
            answers_children = answers.findChildren("div", recursive=False)

            if answers_children is not None:           
                for answer in answers_children:
                    
                    answer_content = answer.find("div", {"class": "answer-content"})

                    answer_status = re.search(re.compile(r"<div class=\"answer-status\-label\">[\s]*([^<]+)"), str(answer_content))
                    answer_title = re.search(re.compile(r"<span class=\"text-muted\">[\s]*([^<]+)</span>[\s]*([^<]+)"), str(answer_content))

                    if answer_status is not None and answer_title is not None:
                        if re.match(re.compile(r"Задание[\s]*ожидает[\s]*проверки"), answer_status.group(1)) is not None:                
                            add_to_dictionary_with_arrays(tasks_to_check, answer_title.group(1).strip() + f" {answer_title.group(2).strip()}", url)    
            else:
                add_to_dictionary_with_arrays(tasks_to_check, "Непонятные ответы", url)
        else:
            add_to_dictionary_with_arrays(tasks_to_check, "Нет ответов", url)
    else:
        add_to_dictionary_with_arrays(tasks_to_check, "Не удалось загрузить ответы", url)

#url
#https://school.burimova.ru/pl/user/user/index?uc[segment_id]=0&uc[rule_string]={"type":"user_hasuserproduct","inverted":0,"className":"app::modules::user::models::rule::HasUserProductRule","params":{"linkedRule":{"type":"userproduct_responsible_teacher_rule","inverted":0,"className":"app::components::logic::rule::CustomFieldRule","params":{"value":{"selected_id":["{162564886}"]},"valueMode":null}},"countCondition":null}}

#referrer
#https://school.burimova.ru/pl/user/user/index?uc%5Bsegment_id%5D=0&uc%5Brule_string%5D=%7B%22type%22%3A%22user_hasuserproduct%22%2C%22inverted%22%3A0%2C%22params%22%3A%7B%22linkedRule%22%3A%7B%22type%22%3A%22userproduct_responsible_teacher_rule%22%2C%22inverted%22%3A0%2C%22params%22%3A%7B%22value%22%3A%7B%22selected_id%22%3A%5B%22162624785%22%5D%7D%2C%22valueMode%22%3Anull%7D%7D%2C%22countCondition%22%3A%7B%22checker%22%3A%22nlt%22%2C%22numval%22%3A%22%22%7D%7D%2C%22maxSize%22%3A%22%22%7D
def get_user_studnets(user_id):
    url = "https://school.burimova.ru/pl/user/user/index?uc[segment_id]=0&uc[rule_string]={\"type\":\"user_hasuserproduct\",\"inverted\":0,\"className\":\"app::modules::user::models::rule::HasUserProductRule\",\"params\":{\"linkedRule\":{\"type\":\"userproduct_responsible_teacher_rule\",\"inverted\":0,\"className\":\"app::components::logic::rule::CustomFieldRule\",\"params\":{\"value\":{\"selected_id\":[\"" + user_id + "\"]},\"valueMode\":null}},\"countCondition\":null}}"

    user_id_pattern = re.compile(r"data-user-id=\"([0-9]{9})\"")

    response = s.get(url)

    print(response.text)

    if response.status_code == 200 and len(response.text) != 0:        
        page = BeautifulSoup(response.text, 'lxml')

        list_counter = page.find("ul", {"class":"pagination"})

        if list_counter is None:
            #all in one
            results = re.findall(user_id_pattern, response.text)
            print(results)
        else:
            print(list_counter)


def get_user_session():
    creds = get_creds("login.txt")

    if creds is None:
        input("Press any key to exit")
        exit(1)

    login, password = creds

    print("Connecting to school.burimova.ru...")
    print(f"email: {login}\tpassword: {password}")

    authorization(login.strip(),password.strip())


def main():   
    f = open("my_student_ids.txt", "r")
    currentDate = datetime.datetime.today().strftime("%Y-%d-%m-%H-%M-%S")

    logging.info("Searching...")

    for id in f:
        task_finder(f"https://school.burimova.ru/teach/control/stat/userComments/id/{id.strip()}")

    f.close()

    f = open(f"{currentDate}-tasks.html", "w", encoding="utf-8")
    f.write(string_dictionary_with_arrays(tasks_to_check))
    f.close()    

    logging.info(f"Done! Result filename: {currentDate}-tasks.html")

    f.close()


get_user_session()

#162564886
get_user_studnets("162624785")

#main()

res_string = string_dictionary_with_arrays(tasks_to_check)

input("Press any key to exit")