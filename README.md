这是一个基于aliyun-oss-python-sdk的同步工具，可以指定同步文件的类型。
要使用的话需要租一个阿里云oss2云存储服务，很便宜9rmb/year (40GB,一般来说足够使用了)
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

**注意: 

因为采用动态加载目录的方式,需指定工作目录的name,以此作为分割的依据,例如想把xycode/documents/workspace/目录下的满足过滤条件的文件夹与文件同步到oss2云端,这里的workspace就是工作目录的name,需在config.json中配置好,目前只支持单一name分割,暂时无添加支持多name分割的打算.所以须保持待更新的目录的name一致.

ls命令是多线程的，update也是多线程的，但ls -u命令是单线程得，因此ls适合快速查看待更新文件，如果待更新文件较多，建议使用update命令更新。
ls -u适用于这样的场景：考虑到短时间内不会修改太多文件，因此在ls后列出待更新文件，查看无误后使用ls -u的单线程更新。
