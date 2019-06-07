# -*- coding: UTF-8 -*-


import os, sys
import config




def progress(count, total, status=''):
    bar_len = 60
    filled_len = int(round(bar_len * count / float(total)))

    percents = round(100.0 * count / float(total), 1)
    bar = '=' * filled_len + '-' * (bar_len - filled_len)

    sys.stdout.write('[%s] %s%s ...%s\r' % (bar, percents, '%', status))
    sys.stdout.flush()  # As suggested by Rom Ruben (see: http://stackoverflow.com/questions/3173320/text-progress-bar-in-the-console/27871113#comment50529068_27871113)


def get_args():
    import argparse
    p = argparse.ArgumentParser(description='Upload zip with shapefile to nextgis.com')
    p.add_argument('file', help='Path to zip with shapefile')
    return p.parse_args()

def _get_if_exist(data, key):
    if key in data:
        return data[key]

    return None


if __name__ == '__main__':
    args = get_args()




    URL = config.ngw_url
    AUTH = config.ngw_creds
    GRPNAME = "photos"

    import requests
    from json import dumps
    from datetime import datetime


   #Генерация уникального названия группы ресурсов, если нужно создать новую
    GRPNAME = datetime.now().isoformat() + " " + GRPNAME

    s = requests.Session()


    def req(method, url, json=None, **kwargs):
        """ Простейшая обертка над библиотекой requests c выводом отправляемых
        запросов в stdout. К работе NextGISWeb это имеет малое отношение. """

        jsonuc = None

        if json:
            kwargs['data'] = dumps(json)
            jsonuc = dumps(json, ensure_ascii=False)

        req = requests.Request(method, url, auth=AUTH, **kwargs)
        preq = req.prepare()

        print ""
        print ">>> %s %s" % (method, url)

        if jsonuc:
            print ">>> %s" % jsonuc

        resp = s.send(preq)

        print resp.status_code
        assert resp.status_code / 100 == 2

        jsonresp = resp.json()

        for line in dumps(jsonresp, ensure_ascii=False, indent=4).split("\n"):
            print "<<< %s" % line

        return jsonresp

    # Обертки по именам HTTP запросов, по одной на каждый тип запроса

    def get(url, **kwargs): return req('GET', url, **kwargs)            # NOQA
    def post(url, **kwargs): return req('POST', url, **kwargs)          # NOQA
    def put(url, **kwargs): return req('PUT', url, **kwargs)            # NOQA
    def delete(url, **kwargs): return req('DELETE', url, **kwargs)      # NOQA

    # Собственно работа с REST API

    iturl = lambda (id): '%s/api/resource/%d' % (URL, id)
    courl = lambda: '%s/api/resource/' % URL

    # Создаем группу ресурсов внутри основной группы ресурсов, в которой будут
    # производится все дальнешние манипуляции.
    grp = post(courl(), json=dict(
        resource=dict(
            cls='resource_group',   # Идентификатор типа ресурса
            parent=dict(id=0),      # Создаем ресурс в основной группе ресурсов
            display_name=GRPNAME,   # Наименование (или имя) создаваемого ресурса
        )
    ))

    # Поскольку все дальнейшие манипуляции будут внутри созданной группы,
    # поместим ее ID в отдельную переменную.
    grpid = grp['id']
    grpref = dict(id=grpid)


    # Метод POST возвращает только ID созданного ресурса, посмотрим все данные
    # только что созданной подгруппы.
    get(iturl(grpid))


    # Проходим по файлам, ищем geojson

    filename = 'output.zip'
    print "uploading "+filename

            # Теперь создадим векторный слой из geojson-файла. Для начала нужно загрузить
            # исходный ZIP-архив, поскольку передача файла внутри REST API - что-то
            # странное. Для загрузки файлов предусмотрено отдельное API, которое понимает
            # как обычную загрузку из HTML-формы, так загрузку методом PUT. Последнее
            # несколько короче.
    with open(filename, 'rb') as fd:
        shpzip = put(URL + '/api/component/file_upload/upload', data=fd)


        srs = dict(id=3857)


        vectlyr = post(courl(), json=dict(
                resource=dict(cls='vector_layer', parent=grpref, display_name=os.path.splitext(filename)[0]),
                vector_layer=dict(srs=srs, source=shpzip)
            ))


    #create map mapstyle
    filename = 'avtoturizm.qml'

    with open(filename,'rb') as f:
        #upload attachment to nextgisweb
        req = requests.put(URL + '/api/'+ '/component/file_upload/upload', data=f, auth=AUTH)
        json_data = req.json()
        if args.debug: print json_data

        mapstyle_data = {}
        mapstyle_data['qgis_vector_style'] = {}
        mapstyle_data['qgis_vector_style']['file_upload'] = {}
        mapstyle_data['qgis_vector_style']['file_upload']['id'] = json_data['id']
        mapstyle_data['qgis_vector_style']['file_upload']['mime_type'] = json_data['mime_type']
        mapstyle_data['qgis_vector_style']['file_upload']['size'] = json_data['size']

        mapstyle_data['resource'] = {}
        mapstyle_data['resource']['cls'] = 'qgis_vector_style'
        mapstyle_data['resource']['display_name'] = 'avtoturizm'
        mapstyle_data['resource']['parent'] = {}
        mapstyle_data['resource']['parent']['id'] = vectlyr['id']

        #add attachment to nextgisweb feature
        post_url = URL + '/api/resource/'
        #print post_url
        #print mapstyle_data
        req = requests.post(post_url, data=json.dumps(mapstyle_data), auth=AUTH)
