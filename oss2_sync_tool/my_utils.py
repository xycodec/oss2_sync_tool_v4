import os,shutil,re
import oss2
import time
def date_to_num(GetObjectResult):
	result=' '.join(GetObjectResult.headers['Last-Modified'].split(' ')[1:-1])
	date_result=time.strptime(result,'%d %b %Y %H:%M:%S')
	date_num=time.mktime(date_result)
	return int(date_num)

#将本地文件同步到云端
def update_file(bucket,local_file_path,local_filename,cloud_file_path,cloud_filename):
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
				print('update '+local_filename+'.')
				bucket.put_object(cloud_file_path+cloud_filename,f)#将本地文件更新到云端cloud_file_path+cloud_filename
			else:
				print(cloud_filename+' already up-to-date.')
		else:
			print(cloud_filename+' does not exist,start upload...')
			bucket.put_object(cloud_file_path+cloud_filename,f)#将本地文件上传到云端cloud_file_path+cloud_filename

#判断源文件与临时文件哪个较新
def newer(srcEntry,destEntry):
    statinfo=os.stat(srcEntry)
    src_last_modified_time=int(statinfo.st_mtime)
    statinfo=os.stat(destEntry)
    dest_last_modified_time=int(statinfo.st_mtime)
    return src_last_modified_time>dest_last_modified_time

#扫描目录的函数,并将符合的文件路径存储到src_file_list中
def scan(path,src_file_list,include_suffix):
    if not os.path.exists(path):
        return
    if os.path.isdir(path):#递归到目录
       for entry in os.listdir(path):
           if not entry.split('/')[-1][0] in ['.']:
            scan(path+'/'+entry,src_file_list,include_suffix)
    else:#递归到文件了
        if path.split('.')[-1] in include_suffix or path.split('.')[0]==path:#对于没有后缀的文件如Makefile等
            src_file_list.append(path)
            #print(path)
        
def format(entry):
    while entry.replace('//','/')!=entry:
        entry=entry.replace('//','/')
    return entry