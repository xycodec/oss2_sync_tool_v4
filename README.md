这是一个基于aliyun-oss-python-sdk的代码同步工具，可以指定同步文件的类型。
要使用的话需要租一个阿里云oss2云存储服务，很便宜9rmb/year
因为流量是走的开发者接口，所以流量免费，用来同步一些小文件很划算
我是用来同步代码文件的，当然其他类型的文件也可以。

注意：
使用前须将config.json文件
中的endpoint
accessKeyId
accessKeySecret
替换为自己的，以及需要在在oss2控制台上新建一个Bucket
然后将Bucket_name替换为自己的Bucket_name

local_path_list
temp_path
cloud_path
local_workspace_name
temp_cachespace_name
也可一一配置为自己的

**版本4:  

**注意: 

因为采用动态加载目录的方式,需指定工作目录的name,以此作为分割的依据,例如想把xycode/documents/workspace/目录下的满足过滤条件的文件夹与文件同步到oss2云端,这里的workspace就是工作目录的name,需在config.json中配置好,目前只支持单一name分割,暂时无添加支持多name分割的打算.所以须保持待更新的目录的name一致.
