
### HELP cmd line args: 
###
###  -g "US,CA" -l "EN" -k "dental implants, free dentist"
###  -g "ES" -l "ES" -k "implantes dentales"
###  -g "DE" -l "DE" -k "zahnimplantate"
###  -g "DE,DK" -l "DE" -k "zahnimplantate"
###
### SEE `how_to.md`

import sys
import json
import argparse
import datetime

from pathlib import Path
from google.ads.googleads.client import GoogleAdsClient # google-ads
from google.ads.googleads.errors import GoogleAdsException # google-ads

# https://developers.google.com/google-ads/api/reference/data/geotargets
# https://developers.google.com/google-ads/api/docs/targeting/location-targeting
DEFAULT_LOCATION_IDS = ["2840"]  # USA Location ID

# https://developers.google.com/google-ads/api/reference/data/codes-formats#expandable-7
DEFAULT_LANGUAGE_ID  = 1000      # English Language ID
LANGUAGES_CODES      = [{"name":"Arabic","code":"ar","id":1019},{"name":"Bengali","code":"bn","id":1056},{"name":"Bulgarian","code":"bg","id":1020},{"name":"Catalan","code":"ca","id":1038},{"name":"Chinese (simplified)","code":"zh_CN","id":1017},{"name":"Chinese (traditional)","code":"zh_TW","id":1018},{"name":"Croatian","code":"hr","id":1039},{"name":"Czech","code":"cs","id":1021},{"name":"Danish","code":"da","id":1009},{"name":"Dutch","code":"nl","id":1010},{"name":"English","code":"en","id":1000},{"name":"Estonian","code":"et","id":1043},{"name":"Filipino","code":"tl","id":1042},{"name":"Finnish","code":"fi","id":1011},{"name":"French","code":"fr","id":1002},{"name":"German","code":"de","id":1001},{"name":"Greek","code":"el","id":1022},{"name":"Gujarati","code":"gu","id":1072},{"name":"Hebrew","code":"iw","id":1027},{"name":"Hindi","code":"hi","id":1023},{"name":"Hungarian","code":"hu","id":1024},{"name":"Icelandic","code":"is","id":1026},{"name":"Indonesian","code":"id","id":1025},{"name":"Italian","code":"it","id":1004},{"name":"Japanese","code":"ja","id":1005},{"name":"Kannada","code":"kn","id":1086},{"name":"Korean","code":"ko","id":1012},{"name":"Latvian","code":"lv","id":1028},{"name":"Lithuanian","code":"lt","id":1029},{"name":"Malay","code":"ms","id":1102},{"name":"Malayalam","code":"ml","id":1098},{"name":"Marathi","code":"mr","id":1101},{"name":"Norwegian","code":"no","id":1013},{"name":"Persian","code":"fa","id":1064},{"name":"Polish","code":"pl","id":1030},{"name":"Portuguese","code":"pt","id":1014},{"name":"Punjabi","code":"pa","id":1110},{"name":"Romanian","code":"ro","id":1032},{"name":"Russian","code":"ru","id":1031},{"name":"Serbian","code":"sr","id":1035},{"name":"Slovak","code":"sk","id":1033},{"name":"Slovenian","code":"sl","id":1034},{"name":"Spanish","code":"es","id":1003},{"name":"Swedish","code":"sv","id":1015},{"name":"Tamil","code":"ta","id":1130},{"name":"Telugu","code":"te","id":1131},{"name":"Thai","code":"th","id":1044},{"name":"Turkish","code":"tr","id":1037},{"name":"Ukrainian","code":"uk","id":1036},{"name":"Urdu","code":"ur","id":1041},{"name":"Vietnamese","code":"vi","id":1040}]

# https://github.com/googleads/google-ads-python/blob/main/google-ads.yaml
YAML_PATH            = "./google-ads.yaml" # Google Ads Credintals

# `default` (returns google response as is) or `table` (returns pandas dataFrame) 
#   or `dict`|`list` (returns optimized dict array) or `compact` (returns compact dict array) or `text`
DEFAULT_IDEAS_OUT_AS = "dict"              


def __get_ideas__(client: GoogleAdsClient, customer_id: str, geo_targets: str | list, language_id: int, keywords: str | list | None, page_url: str | None, **kwargs) -> dict:
    '''
    @kwargs:
    - adult: False|True
    - with_annotations: False|True
    '''
    
    keyword_plan_idea_service = client.get_service("KeywordPlanIdeaService")
    # keyword_competition_level_enum = (client.enums.KeywordPlanCompetitionLevelEnum) # -- where it used?
    keyword_plan_network = (client.enums.KeywordPlanNetworkEnum.GOOGLE_SEARCH_AND_PARTNERS)
    # geo_targets = __map_locations_ids_to_resource_names__(client, geo_targets) # -- not need
    language_id = client.get_service("GoogleAdsService").language_constant_path(language_id)
    keyword_annotation = (client.enums.KeywordPlanKeywordAnnotationEnum) # -- deprecated

    if not (keywords or page_url): 
        raise ValueError("At least one of keywords or page URL is required, but neither was specified.")

    # Only one of the fields "url_seed", "keyword_seed", or
    # "keyword_and_url_seed" can be set on the request, depending on whether
    # keywords, a page_url or both were passed to this function.
    request = client.get_type("GenerateKeywordIdeasRequest")
    request.customer_id = str(customer_id)
    request.language = language_id
    request.geo_target_constants.extend(geo_targets)
    request.include_adult_keywords = bool(kwargs.get('adult', False))
    request.keyword_plan_network = keyword_plan_network
    if bool(kwargs.get('with_annotations', False)): request.keyword_annotation = keyword_annotation # -- deprecated

    if keywords and type(keywords) is str: keywords = list(set([kw.strip() for kw in keywords.split(',')]))

    # To generate keyword ideas with only a page_url and no keywords we need
    # to initialize a UrlSeed object with the page_url as the "url" field.
    if not keywords and page_url: request.url_seed.url = page_url

    # To generate keyword ideas with only a list of keywords and no page_url
    # we need to initialize a KeywordSeed object and set the "keywords" field
    # to be a list of StringValue objects.
    if keywords and not page_url: request.keyword_seed.keywords.extend(keywords)

    # To generate keyword ideas using both a list of keywords and a page_url we
    # need to initialize a KeywordAndUrlSeed object, setting both the "url" and
    # "keywords" fields.
    if keywords and page_url:
        request.keyword_and_url_seed.url = page_url
        request.keyword_and_url_seed.keywords.extend(keywords)

    keyword_ideas = keyword_plan_idea_service.generate_keyword_ideas(request=request)
    
    # if __name__ == "__main__":
    #     for idea in keyword_ideas:
    #         print(f'- "{idea.text}" has "{idea.keyword_idea_metrics.avg_monthly_searches}" avg monthly searches & "{idea.keyword_idea_metrics.competition}" competition.\n')

    return keyword_ideas


def __map_locations_ids_to_resource_names__(client, location_ids):
    """
    Converts a list of location IDs to resource names.
    @client: an initialized GoogleAdsClient instance.
    @location_ids: a list of location ID strings.
    Returns:
        a list of resource name strings using the given location IDs.
    """
    
    if location_ids and type(location_ids) is str: location_ids = list(set([l.strip() for l in location_ids.split(',')]))
    build_resource_name = client.get_service("GeoTargetConstantService").geo_target_constant_path
    return [build_resource_name(location_id) for location_id in location_ids]


def get_lang_code(code: str) -> int:
    '''
    Find out language codes from ref.
    @code - 2-symbols lang code (ex: `en`, `es` or `zh_CN`)
    '''
    
    code = 'en' if not code else str(code).lower()
    for e in LANGUAGES_CODES:
        if e['code'] == code: return e['id']
        if e["name"].lower() == code: return e['id']
        if str(e['id']) == code: return e['id']
    return None


def get_geo_targets(client: GoogleAdsClient, names: str | list, what: str = 'Country', locale: str | None = None, country_code: str | None = None):
    '''
    Find out geos names.
    @names - geo names (ex: `US` or `US,CA` or `[US,CA]` ...)    
    @what - geo type (None or `Any` or `Country`)
    @locale - lang locale (ex: None or `en` or `es` or `zh_CN` ...)
    @country_code - country code 2-symbols iso (ex: `US` or `CA` ...)
    '''
    
    gtc_service = client.get_service("GeoTargetConstantService")
    gtc_request = client.get_type("SuggestGeoTargetConstantsRequest")
    if locale: gtc_request.locale = locale
    if country_code: gtc_request.country_code = country_code

    if type(names) is str: names = list(set([n.strip().upper() for n in names.split(',')]))
    gtc_request.location_names.names.extend(names)
    results = gtc_service.suggest_geo_target_constants(gtc_request)

    res = []
    for suggestion in results.geo_target_constant_suggestions:
        tc = suggestion.geo_target_constant
        if what in [None,'','Any']: res.append(tc.resource_name)
        elif tc.target_type == what:
            if what == 'Country' and tc.country_code.upper() in names: 
                res.append(tc.resource_name)
        if __name__ == "__main__":
            print(f"- get_geo_targets: {tc.resource_name}: ({tc.name}, {tc.country_code}, {tc.target_type}, "
                  f"{tc.status}) -- locale `{suggestion.locale}` by `{suggestion.search_term}`.")
    
    if results.geo_target_constant_suggestions and __name__ == "__main__": print()
    return res    


def get_keyword_ideas(geos: str | list = 'US,CA', lang: str = 'EN', keywords: str | list | None = 'dental implants, free implants', page_url: str | None = None, **kwargs) -> list | None:
    '''
    API Keyword Planner Call (Get Keyword Ideas).
    @geos - countries ISO (ex: `US` or `US,CA` or `[US,CA]` ...) or other geo names
    @lang - language code 2-symbols from ref (ex: `en` or `es` or `zh_CN`)
    @keywords - keywords to search (ex: `dental implants` or `dental implants,free implants` or `[dental implants,free implants]`); max 10
    @page_url - site to filter unrelated keywords (http://... or https://...)
    @kwargs:
      MAIN:
       - yaml_path - path to `./google-ads.yaml` file (use credintals instead of)      
       - credintals - None|`file`|`env`|yaml_config_string|dict (Configuration data used to initialize a GoogleAdsClient, instead of yaml_path)
       - customer_id - Google Ads Customer ID Account Number (format: XXXXXXXXXX not XXX-XXX-XXXX, instead of in credintals or yaml file)      
       - out_as - `default` (returns google response as is) or `table` (returns pandas dataFrame) or `dict`|`list` (returns optimized dict array) or `compact` (returns compact dict array) or `text`
      OPTINONAL:
       - adult: True (include adult keywords)
      DEPRECATED:
       - with_annotations: True (include keywords annotations)
      PROCESSING:
       - with_null_geos: True (no pass DEFAULT_LOCATION_IDS if geos not found)      
       - with_null_lang: True (no pass DEFAULT_LANGUAGE_ID if lang not found)   
       - proccessing: dict for set out processing parameters
      SAVE AS:
       - csv_file - save to csv, uses with out_as = `table`
       - excel_file - save to excel, uses with out_as = `table`
       - html_file - save to html, uses with out_as = `table`
    '''
    
    # init GoogleAdsClient
    if (credintals := kwargs.get('credintals')) and not credintals in ['yaml','file']:
        if credintals == 'env': gc = GoogleAdsClient.load_from_env(version="v17")
        elif type(credintals) is str: gc = GoogleAdsClient.load_from_string(credintals,version="v17")
        elif type(credintals) is dict: gc = GoogleAdsClient.load_from_dict(credintals,version="v17")
        else: raise Exception('Unknown credintals')
    else:
        yaml_path = kwargs.get("yaml_path",YAML_PATH)   
        if not yaml_path or not (cfg_file := Path(yaml_path)) or not cfg_file.is_file():
            if __name__ == "__main__":
                from get_refresh_token import get_refresh_token
                get_refresh_token()
                sys.exit(2)
            raise Exception(f'Yaml Config not Found: {yaml_path}')
        gc = GoogleAdsClient.load_from_storage(path=yaml_path,version="v17")          

    # collect search parameters
    customer_id = kwargs.get('customer_id') or gc.login_customer_id
    geos = get_geo_targets(gc, geos) or get_geo_targets(gc, None if kwargs.get('with_null_geos') == True else DEFAULT_LOCATION_IDS)
    if geos: geos = list(set(geos))
    lang = get_lang_code(lang) or (None if kwargs.get('with_null_lang') == True else DEFAULT_LANGUAGE_ID) 
    out_as = kwargs.get('out_as', DEFAULT_IDEAS_OUT_AS)
    
    # pass out parameters
    if (pr := kwargs.get('proccessing')) and type(pr) is dict: 
        pr['customer_id'] = customer_id
        pr['geos'] = geos
        pr['lang'] = lang
        pr['keywords'] = keywords
        pr['page_url'] = page_url

    # get keyword ideas
    list_keywords = __get_ideas__(gc, customer_id, geos, lang, keywords, page_url, **kwargs)    

    if list_keywords and out_as == 'table': # as table grid (for console or sav to excel|csv|html)
        import pandas as pd
        if list_keywords.total_size == 0: return pd.DataFrame()
        results = list_keywords.results        
        list_to_out = []
        for x in range(len(results)):
            list_months = []
            list_searches = []
            list_annotations = []
            for y in results[x].keyword_idea_metrics.monthly_search_volumes:
                list_months.append(f'{y.year}-{str(y.month-1).zfill(2)}')
                list_searches.append(y.monthly_searches)
            for y in results[x].keyword_annotations.concepts:
                list_annotations.append(y.concept_group.name) 
            list_to_out.append([
                     results[x].text, 
                     results[x].keyword_idea_metrics.avg_monthly_searches, 
                     str(results[x].keyword_idea_metrics.competition), 
                     results[x].keyword_idea_metrics.competition_index, 
                     ', '.join(str(i) for i in list_searches), 
                     ', '.join(str(i) for i in list_months), 
                     ', '.join(str(i) for i in list_annotations),
                     results[x].keyword_idea_metrics.low_top_of_page_bid_micros,
                     results[x].keyword_idea_metrics.high_top_of_page_bid_micros, ])
        df = pd.DataFrame(list_to_out, columns = ["Keyword", "Avg Monthly Searches", "Competition Level", "Competition Index", "Searches Past Months", "Past Months", "List Annotations", "PBM Lo Top", "PBM Hi Top"])
        if s2 := kwargs.get('excel_file'): df.to_excel(s2, header=True, index=False)
        if s2 := kwargs.get('csv_file'): df.to_csv(s2, index=False)
        if s2 := kwargs.get('html_file'): df.to_html(s2, index=False)
        if kwargs.get('shortly', False) == True:
            pd.set_option('display.max_rows', None)
            pd.set_option('display.max_columns', None)
            pd.set_option('display.width', 200)
            pd.set_option('display.max_colwidth', None)
            setattr(df, 'shortly', df.loc[:,["Keyword", "Avg Monthly Searches", "Competition Level", "Competition Index", "PBM Lo Top", "PBM Hi Top"]])
        return df
    
    if list_keywords and out_as in ['dict','list']: # optimized dict array
        if list_keywords.total_size == 0: return None
        results = list_keywords.results
        list_to_out = []
        for x in range(len(results)):
            list_months = []
            list_searches = []
            list_annotations = []
            for y in results[x].keyword_idea_metrics.monthly_search_volumes:
                list_months.append(f'{y.year}-{str(y.month-1).zfill(2)}')
                list_searches.append(y.monthly_searches)        
            for y in results[x].keyword_annotations.concepts:
                list_annotations.append(y.concept_group.name)                
            list_to_out.append({
                    "keyword":      results[x].text, 
                    "avg_monthly_searches": results[x].keyword_idea_metrics.avg_monthly_searches, 
                    "comp_level":   str(results[x].keyword_idea_metrics.competition), 
                    "comp_index":   results[x].keyword_idea_metrics.competition_index, 
                    "searches":     list_searches, 
                    "past_months":  list_months, 
                    "annotations":  list_annotations,
                    "low_top_of_page_bid_micros": results[x].keyword_idea_metrics.low_top_of_page_bid_micros,
                    "high_top_of_page_bid_micros": results[x].keyword_idea_metrics.high_top_of_page_bid_micros, })
        return list_to_out        
    
    if list_keywords and out_as == 'compact': # compact optimized dict array
        if list_keywords.total_size == 0: return None
        results = list_keywords.results
        list_to_out = []
        for x in range(len(results)):
            list_to_out.append({
                    "keyword":      results[x].text, 
                    "avg_monthly_searches": results[x].keyword_idea_metrics.avg_monthly_searches, 
                    "comp_level":   str(results[x].keyword_idea_metrics.competition), 
                    "comp_index":   results[x].keyword_idea_metrics.competition_index, })
        return list_to_out
    
    if list_keywords and out_as == 'text': # text, keyword with info perline (for console)
        if list_keywords.total_size == 0: return ''
        results = list_keywords.results
        text_to_out = ''
        for idea in results:
            text_to_out += f'- "{idea.text}" has "{idea.keyword_idea_metrics.avg_monthly_searches}" avg monthly searches & "{idea.keyword_idea_metrics.competition}" competition.\n'
        return text_to_out

    return list_keywords # google response as is (bad format)
     

if __name__ == "__main__":
    
    parser = argparse.ArgumentParser(description="Generates keyword ideas from a list of seed keywords")
    parser.add_argument("-g","--geos",type=str,required=True,help="Comma Separated ISO Country Codes",)
    parser.add_argument("-l","--lang",type=str,required=True,help="2-Symbols language code",)
    parser.add_argument("-k","--keywords",type=str,required=True,help="Comma Separated Keywords to search",)
    parser.add_argument("-p","--page_url",type=str,required=False,help="Site to filter unrelated keywords",)
    
    args = None
    try: args = parser.parse_args()
    except: print()

    try: 
        
        if args:
            started = datetime.datetime.utcnow()
            proccessing = {'started': str(started)}
            results = get_keyword_ideas(
                    args.geos, args.lang, args.keywords, args.page_url,
                    out_as='table', shortly=True, proccessing=proccessing,
                    csv_file = f'./last_results.csv', )             
            print()
            if proccessing:
                proccessing['finished'] = str(datetime.datetime.utcnow())
                proccessing['elapsed'] = str(datetime.datetime.utcnow() - started)
                print('Processing parameters:\n')
                for k,v in proccessing.items(): print(f' - {k}: {v}')
                print()
            try: 
                print(f'Results (see file `./last_results.csv`) {type(results)}:\n')
                if results in [None,[],0,'']: print('RESULT IS EMPTY') 
                else: raise Exception('')
            except:
                if type(results) is list: print(json.dumps(results,indent=1))
                elif hasattr(results, 'shortly'): print(results.shortly)
                else: print(results)
                
            print('\nTo call from code see `def get_keyword_ideas`')

    except GoogleAdsException as ex:
        
        print(f'Request ID "{ex.request_id}" failed, status "{ex.error.code().name}", details:')
        for error in ex.failure.errors:
            print(f' - {error.message}')
            if error.location:
                for field_path_element in error.location.field_path_elements:
                    print(f" - - on field: {field_path_element.field_name}")
        
    print()
    input('Press Enter to Exit')