#######################################################################    
#######    ИНСТРУКЦИЯ ПО ЗАПОЛНЕНИЮ ФАЙЛА `google-ads.yaml``    #######    
#######################################################################    


1. Ставим и настраиваем `google-ads`
   >> `pip install google-ads`

   Для работы `GoogleAdsClient` нужен файл настроек Yaml,
   который хранит конфигурацию для подключения к сервисам Google.
      
   Для инициализации `GoogleAdsClient` нужны 5 параметров:     
	   - `developer_token` (Basic or Standard access)    
	   - `client_id`    
	   - `client_secret`    
	   - `refresh_token`    
	   - `login_customer_id`    
   
2. Чтобы получить developer_token нужно зайти в управляющий аккаунт    
   https://ads.google.com/intl/ru/home/tools/manager-accounts/?hl=ru    
   в поле поиска ввести `API Center` и открыть найденную страницу.    
   Следуя инструкциям, создать токен.    
	   
3. Чтобы получить `client_id` и `client_secret` необходимо создать проект    
   https://console.cloud.google.com/project    
   Потом зайти в `settings` проекта, в поле поиска ввести `credintals`,     
   в результатах выбрать `APIs & Services Credintals`.    
   Нажать `+ Create credintals` и выбрать `OAuth Client ID`.    
   Заполнить все необходимые данные, в т.ч. добавить тестового пользователя.    

   В итоге мы получим `client id` и `client secret`, которые надо скачать в виде JSON файла    
   и сохранить как `./google_oauth.json`. Файл понадобится для следующего шага.    
	   
4. Чтобы получить `refresh_token` Необходимо:    
   Запустить `get_refresh_token.py -f "./google_oauth.json"`    
   Следовать инструкциям, по окончанию скопировать refresh_token из окна консоли.    
	   
5. Получить `login_customer_id` (это ID аккаунта рекламы) вида `XXX-XXX-XXXX`    
   https://ads.google.com/intl/en/home/tools/manager-accounts/    
   Записать его без дефисов `-`    

6. Все полученные на предыдущих шагах значения сохранить в Yaml файл `./google-ads.yaml`    
   Скачиваем шаблон https://github.com/googleads/google-ads-python/blob/main/google-ads.yaml    
   и сохраняем его как `./google-ads.yaml`    
   P.S: `use_proto_plus` устанавливаем в `False`    

7. Запустить `get_refresh_token.py` для проверки валидности файла и всех параметров.    


#######################################################################    
###########   ИНСТРУКЦИЯ ПО ПОЛУЧЕНИЮ ИДЕЙ КЛЮЧЕВЫХ СЛОВ    ###########    
#######################################################################    


1. Запустить `get_keyword_ideas.py` со следующими параметрами:    
   
   `-g` - Список двухзначных ISO кодов стран, например: `US` или `US,CA`    
   `-l` - 2-х значный код языка, например: `en` или `es` или `zh_CN`    
   `-k` - Список ключевых слов разделенной запятой, например: `dental implants` или `dental implants, free implants`    
   `-p` - [опционально], site to filter unrelated keywords    

   Скрипт читает credintals из Yaml файла `./google-ads.yaml`    
   На выходе будет таблица ключевиков, также сформируется файл `last_results.csv`.    

   Пример: `get_keyword_ideas.py -g "US,CA" -l "EN" -k "dental implants, free dentist"`    
   Пример: `get_keyword_ideas.py -g "ES" -l "ES" -k "implantes dentales"`    
   Пример: `get_keyword_ideas.py -g "DE" -l "DE" -k "zahnimplantate"`    
   Пример: `get_keyword_ideas.py -g "DE,DK" -l "DE" -k "zahnimplantate"`    

2. Для вызова из кода см. ф-ию `get_keyword_ideas`:    

    def `get_keyword_ideas`(`geos`: str | list = `US,CA`, `lang`: str = `EN`, `keywords`: str | list | None = `dental implants, free implants`, `page_url`: str | None = None, `**kwargs`) -> list | None:    
        '''    
        API Keyword Planner Call (Get Keyword Ideas).    
        @`geos` - Список двухзначных ISO кодов стран, например: `US` или `US,CA`    
        @`lang` - 2-х значный код языка, например: `en` или `es` или `zh_CN`    
        @`keywords` - Список ключевых слов разделенной запятой, например: `dental implants` или `dental implants, free implants`    
        @`page_url` - site to filter unrelated keywords (`http://...` or `https://...`)    
        @`kwargs`:    
          ОСНОВНЫЕ:    
           - `yaml_path` - Путь к Yaml файлу `./google-ads.yaml` (если не указаны `credintals`)          
           - `credintals` - None|`file`|`env`|yaml_config_string|dict (Конфигурация для инициализации GoogleAdsClient, задаются вместо Yaml файла)    
           - `customer_id` - Google Ads Customer ID (в формате: XXXXXXXXXX not XXX-XXX-XXXX, если нужно указать другой, не тот что в credintals или yaml Yaml файле)          
           - `out_as` - `default` (возвращается ответ гугла как есть) or `table` (возвращается pandas dataFrame) or `dict`|`list` (возвращается массив dict) or `compact` (возвращается сокращенный массив dict) or `text`    
          ДОПОЛНИТЕЛЬНЫЕ:    
           - `adult`: True (взрослый контент)    
          НЕ ИСПОЛЬЗУЕМЫЕ:    
           - `with_annotations`: True (с аннотациями; не работает на текущей версии!)    
          ПРОЦЕССИНГ:    
           - `with_null_geos`: True (не устанавливать geo в DEFAULT_LOCATION_IDS если страна не найдена)          
           - `with_null_lang`: True (не устанавливать язык в DEFAULT_LANGUAGE_ID если язык не найден)       
           - `proccessing`: dict для вывода параметров для поиска (преимущественно geos и lang); подробнее см. `get_keyword_ideas.py` и вывод в консоль    
        '''

    `@kwargs`[`credintals`] могут быть:     
        -  None  - ищется Yaml файл `./google-ads.yaml`    
        - `file` - ищется Yaml файл `./google-ads.yaml`    
        - `env`  - параметры берутся из переменной окружения;    
                   имена должны быть те же что и в Yaml файле но с префиксом `google_ads_`,    
                   Например:     
                     `use_proto_plus=False` -> `google_ads_use_proto_plus=False`    
                     `login_customer_id=XXXXXXXXXX` -> `google_ads_login_customer_id=XXXXXXXXXX`    
                     `developer_token=...` -> `google_ads_developer_token=...`                        
        - yaml_config_string - передается содержимое Yaml файла с параметрами    
        - dict   - передается словарь с параметрами (имена должны быть те же что и в Yaml файле)    
