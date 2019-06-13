这是一个基于aliyun-oss-python-sdk的代码同步工具，可以指定同步文件的类型。
要使用的话需要租一个阿里云oss2云存储服务，很便宜9rmb/year
因为流量是走的开发者接口，所以流量免费，用来同步一些小文件很划算
我是用来同步代码文件的，当然其他类型的文件也可以。

注意：
使用前须将
endpoint
accessKeyId
accessKeySecret
替换为自己的，以及需要在在oss2控制台上新建一个Bucket
然后将Bucket_name替换为自己的Bucket_name
auth=oss2.Auth(accessKeyId,accessKeySecret)
bucket=oss2.Bucket(auth,endpoint,Bucket_name)
