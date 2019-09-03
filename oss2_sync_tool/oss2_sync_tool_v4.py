import os,shutil
import oss2
import logging
import my_utils as utils
import threading
import json

endpoint=''
accessKeyId=''
accessKeySecret=''
local_path_list=[]
temp_path=''
cloud_path=''
include_suffix=[]
exclude_suffix=[]
bucket_name=''
bucket_list=[]
auth=object()
bucket=object()
local_workspace_name=''
temp_cachespace_name=''
show_help_info=True
log_level=''
CThread_num=1
UThread_num=1
def init():
    with open('config.json','r') as f:
        config_info=json.load(f)
        #print(config_info)
        #配置信息
        global endpoint
        global accessKeyId
        global accessKeySecret
        global local_path_list
        global temp_path
        global cloud_path
        global include_suffix
        global exclude_suffix
        global bucket_name
        global bucket_list
        global auth
        global bucket
        global local_workspace_name
        global temp_cachespace_name
        global show_help_info
        global log_level
        global CThread_num
        global UThread_num

        endpoint=config_info['endpoint']
        accessKeyId=config_info['accessKeyId']
        accessKeySecret=config_info['accessKeySecret']
        local_path_list=config_info['local_path_list']
        temp_path=config_info['temp_path']
        cloud_path=config_info['cloud_path']

        include_suffix=config_info['include_suffix']
        exclude_suffix=config_info['exclude_suffix']
        bucket_name=config_info['bucket_name']
        bucket_list=config_info['bucket_list']
        auth=oss2.Auth(accessKeyId,accessKeySecret)
        bucket=oss2.Bucket(auth,endpoint,bucket_name)
        local_workspace_name=config_info['local_workspace_name']
        temp_cachespace_name=config_info['temp_cachespace_name']
        show_help_info=config_info['show_help_info']
        log_level=config_info['log_level']
        CThread_num=config_info['CThread_num']
        UThread_num=config_info['UThread_num']

src_file_list=[]
temp_file_list=[]
lock=threading.Lock()
def generate_cache(src_file_list,temp_file_list):
    for srcEntry,tempEntry in zip(src_file_list,temp_file_list):
        if not os.path.exists(tempEntry):#先看文件存在否?
            lock.acquire()#加锁
            if not os.path.exists('/'.join(tempEntry.split('/')[:-1])):#再看目录存在否
                os.makedirs('/'.join(tempEntry.split('/')[:-1]))
            lock.release()#释放锁
            with open(tempEntry,'w+') as f:#先创建空文件(因为不存在?)
                f.close()

        if utils.newer(srcEntry,tempEntry) or os.path.getsize(tempEntry)==0:#如果源文件较新或目标文件为空文件(可能是之前刚创建的)，才更新
            shutil.copy2(srcEntry,tempEntry)#copy2()会连带着源文件状态(时间戳)一起复制,copy+copystat

def generate_path(base_path,entry,workspace_name):
    #print(entry,workspace_name)
    assert(len(utils.format(entry).split(workspace_name))==2)
    return utils.format(base_path+entry.split(workspace_name)[1])

#扫描源目录,并生成临时存储信息到temp_file_list,然后根据temp_file_list来更新临时文件
def src2temp(temp_path,thread_number=20):
    #1.扫描源目录,并将符合的文件路径存储到src_file_list
    for entry_path in local_path_list:
        utils.scan(entry_path,src_file_list,include_suffix)
    for entry in src_file_list:
        temp_file_list.append(generate_path(temp_path,entry,local_workspace_name))
        #print(temp_path+'/'.join(entry.split('/')[5:]))

    assert(len(src_file_list)==len(temp_file_list))
    #更新临时文件,引入多线程处理
    tmp_s=[]
    tmp_d=[]
    threads=[]
    for i in range(thread_number):
        tmp_s.append(list())
        tmp_d.append(list())
    for i in range(len(src_file_list)):
        tmp_s[i%thread_number].append(utils.format(src_file_list[i]))
        tmp_d[i%thread_number].append(utils.format(temp_file_list[i]))
    for i in range(thread_number):
        threads.append(threading.Thread(target=generate_cache,args=(tmp_s[i],tmp_d[i],)))
    for t in threads:
        t.setDaemon(True)
        t.start()
    for t in threads:
        t.join()


def update_file(temp_file_list,sep_path):
    for entry in temp_file_list:
        #拆分本地目录名和文件名,生成云路径
        tmp_cloud_path=generate_path(cloud_path,entry,sep_path)
        #print(tmp_cloud_path)
        utils.update_file(bucket,
                    '/'.join(entry.split('/')[:-1])+'/',
                    entry.split('/')[-1],
                    '/'.join(tmp_cloud_path.split('/')[:-1])+'/',
                    tmp_cloud_path.split('/')[-1])

        #print('/'.join(entry.split('/')[:-1])+'/'+entry.split('/')[-1])
        #print((cloud_path+'/'.join(entry.split('/')[5:-1])+'/').replace('//','/')+entry.split('/')[-1])#//会导致云端生成空目录,所以替代
        

#将临时文件同步更新到云端,不直接从源文件同步到云端,做了隔离,对源文件只有read权限,对临时文件才有write权限
def temp2cloud(endpoint,accessKeyId,accessKeySecret,thread_number):
    #扫描源目录,并生成临时存储信息到temp_file_list,然后根据temp_file_list来更新临时文件
    src2temp(temp_path,CThread_num)
    #if not bucket.object_exists(cloud_path):
    #    bucket.put_object(cloud_path)
    
    tmp_c=[]
    threads=[]
    total_size=0
    for i in range(thread_number):
        tmp_c.append(list())
    for i in range(len(temp_file_list)):
        tmp_c[i%thread_number].append(temp_file_list[i])
        if os.path.exists(temp_file_list[i]):
            total_size+=os.path.getsize(temp_file_list[i])
            # print(os.path.getsize(temp_file_list[i]))
        else:
            print('ERROR: '+temp_file_list[i]+' not exist!')
    for i in range(thread_number):
        threads.append(threading.Thread(target=update_file,args=(tmp_c[i],temp_cachespace_name,)))#特别注意要有逗号
    for t in threads:
        t.setDaemon(True)
        t.start()
    for t in threads:
        t.join()
    
    print('scan file number: {0}\ntotal size: {1} KB'.format(len(temp_file_list),total_size/1000))



def print_info():
    print('*************** oss2_sync_tool_v4 ***************************')
    print('* input ls:  list the files that need to be updated.        *')
    print('* input ls -u:  update list after execute ls.               *')
    print('* input update:  update all files.                          *')
    print('* input cfg-s:  configure include_suffix.                   *')
    print('* input cfg-n:  configure oss2-bucket-name.                 *')
    print('* input restore:  restore to the original state.            *')
    print('* input clear:  clear all temp files.                       *')
    print('* input show-info:  set up display help information or not. *')
    print('* input help:  show the help information.                   *')
    print('* input q:  exit the program.                               *')
    print('******************************************* --xycode ********')

ls_update_list=[]#待更新列表
def ls_part(ls_list):
    for entry in ls_list:#ls_list相当于之前的src_file_list
        temp_cloud_path=generate_path(cloud_path,entry,local_workspace_name)
        entry=utils.format(entry)
        #print(temp_cloud_path)
        if not bucket.object_exists(temp_cloud_path):#云端不存在的话
            #print(entry,end='')
            #print("\033[0;31;40m ,Size: {0} KB.\033[0m".format(str(os.path.getsize(entry)/1000))) 
            print(entry+', SIZE: '+str(os.path.getsize(entry)/1000)+' KB.')
            generate_cache([entry],[generate_path(temp_path,entry,local_workspace_name)])#先生成缓存
            if not generate_path(temp_path,entry,local_workspace_name) in ls_update_list:#防止重复添加
            	ls_update_list.append(generate_path(temp_path,entry,local_workspace_name))
            continue
        statinfo=os.stat(entry)
        local_last_modified_time=int(statinfo.st_mtime)-28800#统一时间戳以秒为单位,北京时间-8小时=GMT
        cloud_last_modified_time=utils.date_to_num(bucket.get_object(temp_cloud_path))
        if local_last_modified_time>cloud_last_modified_time:#本地文件较新
            #print(entry,end='')
            #print("\033[0;31;40m ,Size: {0} KB.\033[0m".format(str(os.path.getsize(entry)/1000)))
            print(entry+', SIZE: '+str(os.path.getsize(entry)/1000)+' KB.')
            shutil.copy2(entry,generate_path(temp_path,entry,local_workspace_name))
            if not generate_path(temp_path,entry,local_workspace_name) in ls_update_list:#防止重复添加
                ls_update_list.append(generate_path(temp_path,entry,local_workspace_name))


def ls(thread_number=20):
    ls_list=[]#存放扫描的结果
    for entry_list in local_path_list:
        utils.scan(entry_list,ls_list,include_suffix)
    tmp_l=[]
    threads=[]
    for i in range(thread_number):
        tmp_l.append(list())
    for i in range(len(ls_list)):#分配任务
        tmp_l[i%thread_number].append(ls_list[i])
    for i in range(thread_number):
        threads.append(threading.Thread(target=ls_part,args=(tmp_l[i],)))#特别注意要有逗号
    for t in threads:
        t.setDaemon(True)
        t.start()
    for t in threads:
        t.join()


def clear():
    str=input('clear all temp file?(y/n)\n')
    if str in ['Y','y']:
        if os.path.exists(temp_path):
            shutil.rmtree(temp_path)
        os.makedirs(temp_path)
    else:
        return

store_include_suffix=[]
def cfg_suffix():
    global include_suffix #注意global
    global store_include_suffix
    store_include_suffix=include_suffix.copy()
    include_suffix.clear()
    s=input('please input suffix-name,separated by space:\n')
    include_suffix=s.split(' ')

'''
以后可以考虑用命令设置
endpoint
accessKeyId
accessKeySecret
bucket name
以及用命令恢复
'''
def restore():
    global include_suffix#注意global
    global store_include_suffix#注意global
    include_suffix=store_include_suffix.copy()


def interact(temp_show_help_info):
    if temp_show_help_info: print_info()
    command=input('please input a legal commmad:\n')
    if command=='ls':
        ls(UThread_num)
        if temp_show_help_info:
            interact(True)
        else:
            interact(False)
    elif command=='ls -u':#ls -u需配合ls命令来使用,考虑到ls得到的文件数目较少,因此采取单线程更新,如果要更新大量文件,请采用update命令,ls命令更多的是一种查看待更新文件的命令,其搭配update命令来使用也是可以的
        if ls_update_list==[]:
            print("ls_update_list is empty,no need to update.")
            print("please check for updates to execute command \'ls\' firstly.")
        else:
            update_file(ls_update_list,temp_cachespace_name)
        ls_update_list.clear()
        if temp_show_help_info:
            interact(True)
        else:
            interact(False)
    elif command=='cfg-s':
        cfg_suffix()
        if temp_show_help_info:
            interact(True)
        else:
            interact(False)
    elif command=='cfg-n':
        global bucket
        oss2_bucket_name=input('please input oss2-bucket-name:\n(legal name: '+str(bucket_list)+'\n')
        if oss2_bucket_name in ['xycode1','xycode2']:
            bucket=oss2.Bucket(auth,endpoint,oss2_bucket_name)
        else:
            print('illegal oss2-bucket-name!')
        if temp_show_help_info:
            interact(True)
        else:
            interact(False)
    elif command=='restore':
        restore()
        print('restore OK.')
        if temp_show_help_info:
            interact(True)
        else:
            interact(False)
    elif command=='update':
        src_file_list.clear()
        temp_file_list.clear()
        if not os.path.exists(temp_path):
            os.makedirs(temp_path)
        #src2temp(temp_path)
        temp2cloud(endpoint,accessKeyId,accessKeySecret,UThread_num)
        if temp_show_help_info:
            interact(True)
        else:
            interact(False)
    elif command=='clear':
        clear()
        if temp_show_help_info:
            interact(True)
        else:
            interact(False)
    elif command=='help':
        print_info()
        if temp_show_help_info:
            interact(True)
        else:
            interact(False)
    elif command=='show-info':
        s=input('show?(y/n)\n')
        if s in ['Y','y','yes','Yes','YES']:
            interact(True)
        else:
            interact(False)
    elif command in ['q','exit','quit']:
        return
    elif len(command)==0:
        if temp_show_help_info:
            interact(True)
        else:
            interact(False)
    else:
        print('incorrect command,please input again.')
        if temp_show_help_info:
            interact(True)
        else:
            interact(False)


if __name__ == '__main__':
    init()
    log_file_path = "oss2_sync.log"
    # 设置日志等级
    print("log_level: "+log_level)
    if log_level=='NOTSET':
        oss2.set_file_logger(log_file_path, 'oss2', logging.NOTSET)
    elif log_level=='DEBUG':
        oss2.set_file_logger(log_file_path, 'oss2', logging.DEBUG)
    elif log_level=='INFO':
        oss2.set_file_logger(log_file_path, 'oss2', logging.INFO)
    elif log_level=='WARNING':
        oss2.set_file_logger(log_file_path, 'oss2', logging.WARNING)
    elif log_level=='ERROR':
        oss2.set_file_logger(log_file_path, 'oss2', logging.ERROR)
    elif log_level=='CRITICAL':
        oss2.set_file_logger(log_file_path, 'oss2', logging.ERROR)
    else:#默认INFO等级
        oss2.set_file_logger(log_file_path, 'oss2', logging.INFO)

    interact(show_help_info)


