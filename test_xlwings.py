import xlwings as xw
#创建操作对象
app=xw.App(visible=False,add_book=False)
#visible  是否打开文件，在Excel软件中显示
#add_book 是否创建新的工作簿，即Excel表(这个表是默认的，未命名状态)
#创建一个工作簿，即Excel表
# wb=app.books.add()
# connect to book
wb = app.books.open("xlwingtest.xlsx")
#创建一个sheet工作表
sht=wb.sheets['sheet1']
#给单元格创建一个值
sht.range('A1').value='我给了单元格A1一个值2'
#保存Excel,保存创建的工作簿，如果文件存在，则会覆盖原文件

#给连续的行写入值,从A2开始按行写
sht.range('A2').value=[1,2,3,4,44,7,8]  #sht.range('A2:F2').value=[1,2,3,4,56,7]
#写入行,需要转置
sht.range('B2').options(transpose=True).value=[22,33,44,55]
#插入行列
sht.range('A6').value=[[1,2],[3,4],[5,6]] #默认起点A6，插入三行两列
sht.range('d8').value=["342"]
sht.range('D9').value=[]
sht.range('G8').value = ""
v = sht.range('G8:H8').value
print(v)
print(v == "")


wb.save(r'xlwingtest.xlsx')

#如果资源不关闭，任然还是可以对工作簿进行操作
#后写入的内容需要重新保存
# sht.range('A6').value='我给了单元格A1一个值5'
#wb.save()  #后面的保存不需要传入文件

#关闭Excel程序,
# 如果不关闭资源，重复执行的话，则会生成一个默认的工作簿
wb.close()
app.quit()