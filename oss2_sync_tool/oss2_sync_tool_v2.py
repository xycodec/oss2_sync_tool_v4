import os,shutil,re
import oss2
import logging
import time
import my_utils as utils

#配置信息
endpoint='http://oss-cn-shanghai.aliyuncs.com'
accessKeyId='LTAIdCjJRKVEhRh3'
accessKeySecret='SssX0EYZj6Kr3mOvkSgAgV18KSYtqY'
#local_path='C:/Users/pc/workspace/java workspace/'
local_path_list=['C:/Users/pc/workspace/java workspace/','C:/Users/pc/workspace/sublime/']#因为分割符的位置在下面是硬性指定的,所以最好保证列表中的目录是等深度的,不然就得单独处理
temp_path='C:/Users/pc/update_temp/'
cloud_path='src_test/'

include_suffix=['c','cpp','java','py','txt','xml','properties','h','hpp']

auth=oss2.Auth(accessKeyId,accessKeySecret)
bucket=oss2.Bucket(auth,endpoint,'xycode2')

src_file_list=[]
temp_file_list=[]
#扫描源目录,并生成临时存储信息到temp_file_list中,然后根据temp_file_list来更新临时文件
def src2temp(temp_path):
    #1.扫描源目录,并将符合的文件路径存储到src_file_list中
    for entry_list in local_path_list:
        utils.scan(entry_list,src_file_list,include_suffix)
    for entry in src_file_list:
        temp_file_list.append(temp_path+'/'.join(entry.split('/')[5:]))
        #print(temp_path+'/'.join(entry.split('/')[5:]))

    assert(len(src_file_list)==len(temp_file_list))

    #更新临时文件
    for srcEntry,tempEntry in zip(src_file_list,temp_file_list):
        if not os.path.exists(tempEntry):#先看文件存在否
            if not os.path.exists('/'.join(tempEntry.split('/')[:-1])):#再看目录存在否
                os.makedirs('/'.join(tempEntry.split('/')[:-1]))

            with open(tempEntry,'w+') as f:#先创建空文件(因为不存在)
                f.close()

        if utils.newer(srcEntry,tempEntry) or os.path.getsize(tempEntry)==0:#如果源文件较新或目标文件为空文件(可能是之前刚创建的)，才更新
            shutil.copy2(srcEntry,tempEntry)#copy2()会连带着源文件状态(时间戳)一起复制,copy+copystat


#将临时文件同步更新到云端,不直接从源文件同步到云端,做了一个隔离,对源文件只有读权限,对临时文件才有读写权限
def temp2cloud(endpoint,accessKeyId,accessKeySecret):
    #扫描源目录,并生成临时存储信息到temp_file_list中,然后根据temp_file_list来更新临时文件
    src2temp(temp_path)
    if not bucket.object_exists(cloud_path):
        bucket.put_object(cloud_path)

    total_size=0
    for entry in temp_file_list:
        #拆分本地目录名和文件名,生成云端路径
        utils.update_file(bucket,
                    '/'.join(entry.split('/')[:-1])+'/',
                    entry.split('/')[-1],
                    (cloud_path+'/'.join(entry.split('/')[4:-1])+'/').replace('//','/'),
                    #//会导致云端生成空目录,所以替换
                    entry.split('/')[-1])

        #print('/'.join(entry.split('/')[:-1])+'/'+entry.split('/')[-1])
        #print((cloud_path+'/'.join(entry.split('/')[5:-1])+'/').replace('//','/')+entry.split('/')[-1])#4 or 5?
        total_size+=os.path.getsize(entry)
    print('scan file number: {0}\ntotal size: {0} kB'.format(len(temp_file_list),total_size/1000))



def print_info():
    print('*****************************************************')
    print('* input ls:  list the files that need to be updated.*')
    print('* input update:  update all files.                  *')
    print('* input clear:  clear all temp files.               *')
    print('* input q:  exit the program.                       *')
    print('*****************************************************')

def ls():
    # 设置日志等级
    log_file_path = "log.log"
    oss2.set_file_logger(log_file_path, 'oss2', logging.CRITICAL)
    ls_list=[]
    for entry_list in local_path_list:
        utils.scan(entry_list,ls_list,include_suffix)
    for entry in ls_list:
        #entry=entry.replace('//','/')
        temp_cloud_path=(cloud_path+'/'.join(entry.split('/')[5:-1])+'/').replace('//','/')+entry.split('/')[-1]
        #print(temp_cloud_path)
        if not bucket.object_exists(temp_cloud_path):
            print(entry)
            continue
        statinfo=os.stat(entry)
        local_last_modified_time=int(statinfo.st_mtime)-28800#统一转换为以秒为单位,北京时间-8小时=GMT
        cloud_last_modified_time=utils.date_to_num(bucket.get_object(temp_cloud_path))
        if local_last_modified_time>cloud_last_modified_time:
            print(entry)
    log_file_path = "log.log"
    oss2.set_file_logger(log_file_path, 'oss2', logging.ERROR)

def clear():
    str=input('clear all temp file?(y/n)')
    if str in ['Y','y']:
        if os.path.exists(temp_path):
            shutil.rmtree(temp_path)
        os.makedirs(temp_path)
    else:
        return

def interact():
    print_info()
    command=input('please input a legal commmad:\n')
    if command=='ls':
        ls()
        interact()
    elif command=='update':
        if not os.path.exists(temp_path):
            os.makedirs(temp_path)
        temp2cloud(endpoint,accessKeyId,accessKeySecret)
        interact()
    elif command=='clear':
        clear()
        interact()
    elif command=='q':
        return
    else:
        print('incorrect command,please input again.')
        interact()


if __name__ == '__main__':
    # 设置日志等级
    log_file_path = "log.log"
    oss2.set_file_logger(log_file_path, 'oss2', logging.ERROR)
    interact()


