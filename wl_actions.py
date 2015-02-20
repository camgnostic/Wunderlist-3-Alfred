from wl_utils import addTask, editTask, remTask, remList, addList, notify
from workflow import Workflow
import sys
        

def main(wf):
    #if no args, no query:
    if len(wf.args):
        query = wf.args[0]
    else:
        query = None
    #second OAuth leg calls this as login:
    if query == "login":
        do_login()
    if wf.get_password('token') == None:
        wf.logger.error('no log_in token at wl_actions.py')
        raise RuntimeError('no login information')
    if query != None:
        verb = query.split(":")[0]
        query = ":".join(query.split(":")[1:]).lstrip(":").lstrip(' ')
        if verb == "new":
            if addList(wf, query) != False:
                notify("List " + query + " added successfully!")
            else:
                wf.logger.warning('list add failure')
        if verb == "remlist":
            if remList(wf, query) != False:
                notify("List deleted successfully")
            else:
                wf.logger.warning('list delete failure')
        if verb == "add":
            listid = query.split(":")[0]
            taskname = ":".join(query.split(":")[1:]).lstrip(":").lstrip(' ')
            if addTask(wf, listid, taskname) != False:
                notify('Task ' + taskname + ' added successfully')
            else:
                wf.logger.warning('task add failure')
        if verb in ["done", "star", "rem"]:
            listId = query.split(":")[0]
            taskId = ":".join(query.split(":")[1:]).lstrip(":").lstrip(' ')
            if verb == "star":
                data = editTask(wf, listId, taskId, toggle='star')
                if data != False:
                    notify('Task ' + data['title'] + (' Uns' if data['starred'] == False else ' S') +
                           'tarred successfully')
                else:
                    wf.logger.warning('task star failure')
            if verb == "rem":
                if remTask(wf, listId, taskId) != False:
                    notify("Task deleted")
                else:
                    wf.logger.warning('task delete failure')
            if verb == "done":
                if editTask(wf, listId, taskId, toggle='done') != False:
                    notify("Task marked completed")
                else:
                    wf.logger.warning('task done failure')
    
    
if __name__ == '__main__':
    wf = Workflow()
    sys.exit(wf.run(main))
    