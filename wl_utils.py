from lib import requests
import sys
import os
import json
from workflow import Workflow, PasswordNotFound
from workflow.background import run_in_background, is_running
from wl_auth import do_login, set_token

ICON_ROOT, filename = os.path.split(os.path.abspath(__file__))
ICON_ROOT = os.path.join(ICON_ROOT, 'icons/')
ICON_LIST = os.path.join(ICON_ROOT, 'list.png')
ICON_ITEM = os.path.join(ICON_ROOT, 'item.png')
ICON_STAR = os.path.join(ICON_ROOT, 'star.png')
ICON_UNSTAR = os.path.join(ICON_ROOT, 'unstar.png')
ICON_DELETE = os.path.join(ICON_ROOT, 'deleteitem.png')
ICON_DONE = os.path.join(ICON_ROOT, 'done.png')
ICON_NEWLIST = os.path.join(ICON_ROOT, 'newlist.png')
ICON_ADDTASK = os.path.join(ICON_ROOT, 'newitem.png')
ICON_UPDATE = os.path.join(ICON_ROOT, 'update.png')
ICON_EMPTY = os.path.join(ICON_ROOT, 'empty.png')


api_url = "https://a.wunderlist.com/api/v1/"
    

def getLists(wf, query=False, add=False):
    lists = wf.cached_data('lists', None, max_age=0)
    positions = wf.cached_data('positions', None, max_age=0)
    refreshLists(wf)
    if is_running('updateLists'):
        wf.add_item('Updating lists...', valid=False, icon=ICON_UPDATE)
    if not lists:
        wf.add_item('No lists found', valid=False, icon=ICON_EMPTY)
        wf.send_feedback()
    all_list = [int(x) for x in lists]
    positionless_lists = filter(lambda x: x not in positions, all_list)
    all_positions = positions + positionless_lists
    if query and all_positions:
        new_positions = wf.filter(query, all_positions, key=lambda x: lists[str(x)]['title'], min_score=20)
        if len(new_positions) > 0 or add == False:
            all_positions = new_positions
    if len(all_positions) == 1 and add == False:
        refreshTasks(wf, all_positions[0])
    for list_id in all_positions:
        if str(list_id) in lists:
            title = lists[str(list_id)]['title']
            counts = wf.cached_data('counts:' + str(list_id), None, max_age=0)
            if counts is not None:
                subtitle = 'Completed: ' + str(counts[0]) + ', Remaining: ' + str(counts[1])
            else:
                subtitle = "updating counts..."
            uid = lists[str(list_id)]['id']
            if add == False:
                wf.add_item(title=title, subtitle=subtitle,
                            valid=False, autocomplete=title + ":",
                            icon=ICON_LIST)
            else:
                wf.add_item(title=title, subtitle=u'Add new task',
                            valid=False, autocomplete=u'Add: ' + title + ':' + query,
                            icon=ICON_ADDTASK)
    if query != "" and add == False:
        wf.add_item(title = u'Add', subtitle = u'Add a new task to a list',
                    valid=False, autocomplete="Add:" + query, icon=ICON_ADDTASK)
        wf.add_item(title = u'New', subtitle = u'New list',
                    valid=False, autocomplete="New:" + query, icon=ICON_NEWLIST)
    wf.send_feedback()
    return

def getTasks(wf, listId, listname, query):
    tasks = wf.cached_data('tasks:' + str(listId), None, max_age=0)
    task_positions = wf.cached_data('task_positions:' + str(listId), None, max_age=0)
    refreshTasks(wf, listId)
    if is_running('updateTasks:' + listId):
        wf.add_item(u'Updating tasks...', valid=False, icon=ICON_UPDATE)
    if not tasks:
        wf.add_item(u'No tasks found.', valid=False, icon=ICON_EMPTY)
        all_tasks = []
    else:
        positionless_tasks = [filter(lambda x: x not in task_positions, y) for y in tasks]
        all_tasks = task_positions + positionless_tasks
        if query and tasks:
            all_tasks = wf.filter(query, tasks, lambda x: tasks[x]['title'], min_score=20)
        for task_id in all_tasks:
            if str(task_id) in tasks:
                task = tasks[str(task_id)]
                title = task['title']
                subtitle = ("Not " if task['starred'] != True else "") + "Starred"
                if 'due_date' in task:
                    subtitle += " Due: " + task['due_date']
                else:
                    subtitle += " No due date"
                autocomplete = listname + ": " + title
                if task['starred']:
                    icon = ICON_STAR
                else:
                    icon = ICON_ITEM
                wf.add_item(title=title, subtitle=subtitle, valid=False,
                            autocomplete=autocomplete, icon=icon)
    if len(all_tasks) != 1 or query != tasks[str(all_tasks[0])]['title']:
        valid = False if query == "" else True
        autocomplete = False if query != "" else u'Add: ' + listname + ':' + query
        wf.add_item(title=u'Add:' + query, subtitle=u'Add a new task to list ' + listname,
                     valid=valid, arg = u'add:' + str(listId) + ":" + query,
                     autocomplete=autocomplete, icon=ICON_ADDTASK)
        wf.add_item(title=u'Delete list', subtitle=u'List will be deleted permanently, with all children',
                    valid=True, arg = u'remlist:' + str(listId), icon=ICON_DELETE)
    wf.send_feedback()
            
        
    
def refreshLists(wf, update=False):
    if update == True:
        wf.cache_data('lists', None)
    if not (wf.cached_data_fresh('lists', max_age=600) and
            wf.cached_data_fresh('positions', max_age=600)):
        cmd = ['/usr/bin/python', wf.workflowfile('wl_update.py'), 'lists']
        run_in_background('updateLists', cmd)
        
def refreshTasks(wf, listId, update=False):
    if update == True:
        wf.cache_data('tasks:' + str(listId), None)
    if not (wf.cached_data_fresh('tasks:' + str(listId), max_age=600) and
            wf.cached_data_fresh('task_positions:' + str(listId), max_age=600)):
        cmd = ['/usr/bin/python', wf.workflowfile('wl_update.py'), 'tasks:' + str(listId)]
        run_in_background('updateTasks:' + str(listId), cmd)

def getListId(wf, listname):
    lists = wf.cached_data('lists', None, max_age=0)
    refreshLists(wf)
    for listid, listitem in lists.items():
        if listitem['title'] == listname:
            return listid
    return False

def getTask(wf, listid, taskname):
    tasks = wf.cached_data('tasks:' + str(listid), None, max_age=0)
    if tasks == None:
        return False
    refreshTasks(wf, listid)
    for taskid, taskitem in tasks.items():
        if taskitem['title'] == taskname:
            return taskitem
    return False

def addList(wf, listname):
    url = 'lists'
    params = {'title': listname}
    c = Caller(wf)
    data = c.post(url, params)
    refreshLists(wf, True)
    if data != False:
        return data['id']
    else:
        return False
    
def remList(wf, listid):
    url = 'lists/' + str(listid)
    lists = wf.cached_data('lists', None, max_age=0)
    thisList = lists[str(listid)]
    url += '?revision=' + str(thisList['revision'])
    c = Caller(wf)
    data = c.delete(url)
    refreshLists(wf, True)
    if data != False:
        return True
    else:
        return False
    
def addTask(wf, listid, taskname):
    url = 'tasks'
    params = {'list_id': int(listid), 'title': taskname}
    wf.logger.debug(params)
    c = Caller(wf)
    data = c.post(url, params)
    refreshTasks(wf, listid, True)
    if data != False:
        wf.logger.debug(data)
        return data['id']
    else:
        return data

def editTask(wf, listid, taskid, toggle=False):
    tasks = wf.cached_data('tasks:' + str(listid), None, max_age=0)
    task = tasks[str(taskid)]
    url = "tasks/" + str(taskid)
    params = {'revision': int(task['revision'])}
    if toggle == 'star':
        params['starred'] = not task['starred']
    if toggle == 'done':
        params['completed'] = not task['completed']
    c = Caller(wf)
    data = c.patch(url, params)
    refreshTasks(wf, listid, True)
    return data

def remTask(wf, listid, taskid):
    tasks = wf.cached_data('tasks:' + str(listid), None, max_age=0)
    task = tasks[str(taskid)]
    url = "tasks/" + str(taskid) + "?revision=" + str(task['revision'])
    c = Caller(wf)
    data = c.delete(url)
    refreshTasks(wf, listid, True)
    return data



class Caller(object):
    def __init__(self, wf):
        try:
            self.log = wf.logger
            self.token = wf.get_password('token')
            self.headers = {"X-Access-Token": self.token,
                            "X-Client-ID": wf.settings['api']['client_id'],
                            'content-type': 'application/json'}
        except PasswordNotFound:
            wf.logger.warning('no api key')
            
    def post(self, url, data):
        url = api_url + url
        data = u'' + json.dumps(data)
        r = requests.post(url, data=data, headers=self.headers)
        if r.ok:
            return r.json()
        else:
            self.log.debug(r.text)
            return False
        
    def patch(self, url, data):
        url = api_url + url
        data = u'' + json.dumps(data)
        r = requests.patch(url, data=data, headers=self.headers)
        if r.ok:
            return r.json()
        else:
            self.log.debug(r.text)
            return False
        
    def delete(self, url):
        url = api_url + url
        r = requests.delete(url, headers=self.headers)
        if r.ok:
            return True
        else:
            self.log.debug(r.text)
            return False
         

def notify(msg):
    print(msg)
    