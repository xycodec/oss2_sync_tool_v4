import os,shutil,re
import oss2
import logging
import time

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

def date_to_num(GetObjectResult):
	result=' '.join(GetObjectResult.headers['Last-Modified'].split(' ')[1:-1])
	date_result=time.strptime(result,'%d %b %Y %H:%M:%S')
	date_num=time.mktime(date_result)
	return int(date_num)

#将本地文件同步到云端
def update_file(local_file_path,local_filename,cloud_file_path,cloud_filename):
	statinfo=os.stat(local_file_path+local_filename)
	#注意时区的转换
	# local_last_modified_time=time.mktime(time.localtime(statinfo.st_mtime))-28800#统一转换为以秒为单位,北京时间-8小时=GMT
	local_last_modified_time=int(statinfo.st_mtime)-28800#统一转换为以秒为单位,北京时间-8小时=GMT
	with open(oss2.to_unicode(local_file_path+local_filename),'rb') as f:
		if bucket.object_exists(cloud_file_path+cloud_filename):#云端已经存在该文件
			cloud_last_modified_time=date_to_num(bucket.get_object(cloud_file_path+cloud_filename))
			# print(local_last_modified_time,cloud_last_modified_time)
			if local_last_modified_time>cloud_last_modified_time:
				#如果本地的文件较新才更新到云端
				print('开始更新'+local_filename)
				bucket.put_object(cloud_file_path+cloud_filename,f)#将本地文件更新到云端cloud_file_path+cloud_filename
			else:
				print(cloud_filename+' 已经最新,无需再更新')
		else:
			print(cloud_filename+' 不存在,开始上传')
			bucket.put_object(cloud_file_path+cloud_filename,f)#将本地文件上传到云端cloud_file_path+cloud_filename

#判断源文件与临时文件哪个较新
def newer(srcEntry,destEntry):
    statinfo=os.stat(srcEntry)
    src_last_modified_time=int(statinfo.st_mtime)
    statinfo=os.stat(destEntry)
    dest_last_modified_time=int(statinfo.st_mtime)
    return src_last_modified_time>dest_last_modified_time

#扫描目录的函数,并将符合的文件路径存储到src_file_list中
src_file_list=[]
def scan(path):
    if not os.path.exists(path):
        return
    if os.path.isdir(path):
       for entry in os.listdir(path):
           scan(path+'/'+entry)
    else:
        if path.split('.')[-1] in include_suffix:
            src_file_list.append(path)
            #print(path)

#扫描源目录,并生成临时存储信息到dest_file_list中,然后根据dest_file_list来更新临时文件
dest_file_list=[]
def src2temp(temp_path):
    #1.扫描源目录,并将符合的文件路径存储到src_file_list中
    for entry_list in local_path_list:
        scan(entry_list)
    for entry in src_file_list:
        dest_file_list.append(temp_path+'/'.join(entry.split('/')[5:]))
        #print(temp_path+'/'.join(entry.split('/')[4:]))

    assert(len(src_file_list)==len(dest_file_list))

    #更新临时文件
    for srcEntry,destEntry in zip(src_file_list,dest_file_list):
        #print(srcEntry)
        #print(destEntry)
        if not os.path.exists(destEntry):#先看文件存在否
            if not os.path.exists('/'.join(destEntry.split('/')[:-1])):#再看目录存在否
                os.makedirs('/'.join(destEntry.split('/')[:-1]))
            with open(destEntry,'w+') as f:#先创建空文件
                f.close()

        if newer(srcEntry,destEntry) or os.path.getsize(destEntry)==0:#如果源文件较新或目标文件为空文件(可能是之前创建的)，才更新
            shutil.copy2(srcEntry,destEntry)#copy2()会连带着源文件状态(时间戳)一起复制,copy+copystat


#将临时文件同步更新到云端,为了数据的安全性,不直接从源文件同步到云端,做了一个隔离,对源文件只有读权限,对临时文件才有读写权限
def temp2cloud(endpoint,accessKeyId,accessKeySecret):
    #扫描源目录,并生成临时存储信息到dest_file_list中,然后根据dest_file_list来更新临时文件
    ##先清理临时目录及文件,慎重
    #os.remove()
    src2temp(temp_path)
    if not bucket.object_exists(cloud_path):
        bucket.put_object(cloud_path)

    total_size=0
    for entry in dest_file_list:
        #拆分本地目录名和文件名,生成云端路径
        update_file('/'.join(entry.split('/')[:-1])+'/',entry.split('/')[-1],
                    (cloud_path+'/'.join(entry.split('/')[4:-1])+'/').replace('//','/'),
                    #//会导致云端生成空目录,所以要替换
                    entry.split('/')[-1])

        #print('/'.join(entry.split('/')[:-1])+'/'+entry.split('/')[-1])
        #print((cloud_path+'/'.join(entry.split('/')[4:-1])+'/').replace('//','/')+entry.split('/')[-1])
        total_size+=os.path.getsize(entry)
    print('scan file number: {0}\ntotal size: {0} kB'.format(len(dest_file_list),total_size/1000))

# 设置日志等级
log_file_path = "log.log"
oss2.set_file_logger(log_file_path, 'oss2', logging.ERROR)

temp2cloud(endpoint,accessKeyId,accessKeySecret)





