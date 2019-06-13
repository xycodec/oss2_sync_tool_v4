endpoint=''
accessKeyId=''
accessKeySecret=''
local_path_list=[]
temp_path=''
cloud_path=''
include_suffix=[]
bucket_name=''
auth=object()
bucket=object()
def init():
    with open('config.json','r') as f:
        config_info=json.load(f)
        #配置信息
        global endpoint
        global accessKeyId
        global accessKeySecret
        global local_path_list
        global temp_path
        global cloud_path
        global include_suffix
        global bucket_name
        global auth
        global bucket
        endpoint=config_info['endpoint']
        accessKeyId=config_info['accessKeyId']
        accessKeySecret=config_info['accessKeySecret']
        #local_path='C:/Users/pc/workspace/java workspace/'
        local_path_list=config_info['local_path_list']#因为分割符的位置在下面是�?性指定的,所以最好保证列表中的目录是等深度的,不然就得单独处理
        #'C:/Users/pc/Documents/workspace-sts-3.9.6.RELEASE/'
        temp_path=config_info['temp_path']
        cloud_path=config_info['cloud_path']

        include_suffix=config_info['include_suffix']
        #include_file=['Makefile','makefile']
        bucket_name=config_info['bucket_name']
        auth=oss2.Auth(accessKeyId,accessKeySecret)
        bucket=oss2.Bucket(auth,endpoint,bucket_name)
