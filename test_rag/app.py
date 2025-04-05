from langchain_community.document_loaders import PyPDFLoader
from langchain_openai import OpenAIEmbeddings, ChatOpenAI 
from langchain_chroma import Chroma
from langchain.chains import RetrievalQA
from langchain.text_splitter import RecursiveCharacterTextSplitter
from fastapi import FastAPI, Query,File, UploadFile,Form, Request
from fastapi.middleware.cors import CORSMiddleware
from typing import Optional
from pydantic import BaseModel
import os
import requests
import json 
import yagmail
from models import session,Students,Loan
import os
from PyPDF2 import PdfReader
import docx
import textract
import tempfile

def read_document(file_path):
    ext = os.path.splitext(file_path)[1].lower()
    if ext == '.pdf':
        try:
            reader = PdfReader(file_path)
            text = "\n".join(page.extract_text() for page in reader.pages if page.extract_text())
        except Exception as e:
            return f"PDF read error: {e}"
    elif ext == '.docx':
        try:
            doc = docx.Document(file_path)
            text = "\n".join([para.text for para in doc.paragraphs])
        except Exception as e:
            return f"DOCX read error: {e}"
    elif ext == '.doc':
        try:
            text = textract.process(file_path).decode('utf-8')
        except Exception as e:
            return f"DOC read error (using textract): {e}"
    else:
        return "Unsupported file type."

    return text

d_en={"ECE_G":1500, "CE_G":1500, "ME_G":1500 ,"CSE_G":1500,"MBA":1000,"ECE_B":5000, "CE_B":8000, "ME_B":10000 ,"CSE_B":3000,}
d_nm={"BBA":7.5, "B_M":7.5, "B_P":7.5, "B_C":7.5, "M_M":9.0, "M_P":9.0, "M_C":9.0}
sid=None
api_key = ""
#os.getenv("OPENAI_API_KEY")
em = OpenAIEmbeddings(openai_api_key=api_key)
vectorstore = Chroma(persist_directory="../vector_store_chroma", embedding_function=em)

retriever = vectorstore.as_retriever(search_kwargs={"k": 3})  # Get top 3 similar chunks
llm = ChatOpenAI(model="gpt-4", openai_api_key=api_key)
qa_chain = RetrievalQA.from_chain_type(llm=llm, retriever=retriever)

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["GET"],
    allow_headers=["*"],
)

headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }

class Container(BaseModel):
    promppt: str
    file: UploadFile = File(None)


def A1(qs):
    response = qa_chain.invoke(qs)
    response=response['result']
    data = {
        "model": "gpt-4o-mini",  
        "messages": [
            {"role": "system", "content": "From the content given try to format it in proper structured answer. Donot add extra new information, just provide me structured form of answer only with no other text."},
            {"role": "user", "content": f"The content is : {response}"},
        ],
    }
    answerx = requests.post("https://api.openai.com/v1/chat/completions",headers=headers,data=json.dumps(data))
    answerx = answerx.json()
    
    if "choices" in answerx :
        ans = answerx["choices"][0]["message"]["content"]
    return ans

async def A2(docv,promptt):
    #fileContent = await docv.read() # content
    with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(docv.filename)[1]) as tmp:
        tmp.write(await docv.read())
        tmp_path = tmp.name

    fileContent = read_document(tmp_path)
    os.remove(tmp_path)
    print('ggggggg')
    filecontent=str(fileContent)
    pp=promptt
    print('hre')
    response = qa_chain.invoke(pp)
    response=response['result'] #queried qs
    print('hhhh')
    print(response)
    data = {
        "model": "gpt-4o-mini",  
        "messages": [
            {"role": "system", "content": " From the college criteria and the students details check if student is eligible or not based on the asked question and if not then where he or she lacks . Tell me whether the student is eligible and if not where he lacks, Be sober , if not eligible donot directly say no rather say what details she lacks . Donot give any other information."},
            {"role": "user", "content": f"The college details are : {response} , and the student's details are : {filecontent}, and the question asked by student is {pp} ." }
        ],
    }
    print(data)
    answerx = requests.post("https://api.openai.com/v1/chat/completions",headers=headers,data=json.dumps(data))
    answerx = answerx.json()
    
    if "choices" in answerx :
        ans = answerx["choices"][0]["message"]["content"]
    return ans

def A3(Program='all',Stream='all',var=True):
    j=0
    if Program == 'all' and Stream =='all':
        students = session.query(Students).all()
        for student in students:
            if student.Admission_Status=='Pending':
                if student.Stream in d_en.keys():
                    if  student.ENTRANCE_rank<=d_en[student.Stream] :
                        x=student.Email_ID
                        sender_email = "suneha2003datta@gmail.com"
                        receiver_email = "suvadipbanerjee02@gmail.com"
                        subject = "Admission in XYZ College Update "
                        body = "Dear "+student.Name + "\n This is to inform you that your Admission in XYZ Institute Of Technology for the program "+ student.Program + " and Stream "+student.Stream+" has been accepted. \n You are requested to come to college for counselling on 15th May 2025.\n Regards XYZ Institute Of Technology" 
                        yag = yagmail.SMTP(sender_email, "hevejrxokhqmxswp")
                        yag.send(receiver_email, subject, body)  
                        print('done')
                        student.Admission_Status='Accepted'
                        session.commit()
                        j=j+1
                    else:
                        x=student.Email_ID
                        sender_email = "suneha2003datta@gmail.com"
                        receiver_email = "suvadipbanerjee02@gmail.com"
                        subject = "Admission in XYZ College Update "
                        body = "Dear "+student.Name + "\n This is to inform you that your Admission in XYZ Institute Of Technology for the program "+ student.Program + " and Stream "+student.Stream+" has been not taken under consideration. \n We wish you all the very best for further improvement in your scores .\n Regards XYZ Institute Of Technology" 
                        yag = yagmail.SMTP(sender_email, "hevejrxokhqmxswp")
                        yag.send(receiver_email, subject, body)  
                        print('done')
                        student.Admission_Status='Rejected'
                        session.commit()
                        j=j+1
                else:
                    if  student.ENTRANCE_rank<=d_nm[student.Stream] :
                        x=student.Email_ID
                        sender_email = "suneha2003datta@gmail.com"
                        receiver_email = "suvadipbanerjee02@gmail.com"
                        subject = "Admission in XYZ College Update "
                        body = "Dear "+student.Name + "\n This is to inform you that your Admission in XYZ Institute Of Technology for the program "+ student.Program + " and Stream "+student.Stream+" has been accepted. \n You are requested to come to college for counselling on 15th May 2025.\n Regards XYZ Institute Of Technology" 
                        yag = yagmail.SMTP(sender_email, "hevejrxokhqmxswp")
                        yag.send(receiver_email, subject, body)  
                        print('done')
                        x=student.Email_ID
                        student.Admission_Status='Accepted'
                        session.commit()
                        j=j+1
                    else:
                        x=student.Email_ID
                        sender_email = "suneha2003datta@gmail.com"
                        receiver_email = "suvadipbanerjee02@gmail.com"
                        subject = "Admission in XYZ College Update "
                        body = "Dear "+student.Name + "\n This is to inform you that your Admission in XYZ Institute Of Technology for the program "+ student.Program + " and Stream "+student.Stream+" has been not taken under consideration. \n We wish you all the very best for further improvement in your scores .\n Regards XYZ Institute Of Technology" 
                        yag = yagmail.SMTP(sender_email, "hevejrxokhqmxswp")
                        yag.send(receiver_email, subject, body)  
                        print('done')
                        student.Admission_Status='Rejected'
                        session.commit()
                        j=j+1
        if j==0:
            return 'There is no candidate who have given any application recently.'
        else:
            return 'All candidates have been shortlisted and have been communicated through email.'
    elif Program=='all':
        students = session.query(Students).filter(Students.Stream==Stream).all()
        for student in students:
            if student.Admission_Status=='Pending':
                if student.Stream in d_en.keys():
                    if  student.ENTRANCE_rank<=d_en[student.Stream] :
                        x=student.Email_ID
                        sender_email = "suneha2003datta@gmail.com"
                        receiver_email = "suvadipbanerjee02@gmail.com"
                        subject = "Admission in XYZ College Update "
                        body = "Dear "+student.Name + "\n This is to inform you that your Admission in XYZ Institute Of Technology for the program "+ student.Program + " and Stream "+student.Stream+" has been accepted. \n You are requested to come to college for counselling on 15th May 2025.\n Regards XYZ Institute Of Technology" 
                        yag = yagmail.SMTP(sender_email, "hevejrxokhqmxswp")
                        yag.send(receiver_email, subject, body)  
                        print('done')
                        x=student.Email_ID
                        student.Admission_Status='Accepted'
                        session.commit()
                        j=j+1
                    else:
                        x=student.Email_ID
                        sender_email = "suneha2003datta@gmail.com"
                        receiver_email = "suvadipbanerjee02@gmail.com"
                        subject = "Admission in XYZ College Update "
                        body = "Dear "+student.Name + "\n This is to inform you that your Admission in XYZ Institute Of Technology for the program "+ student.Program + " and Stream "+student.Stream+" has been not taken under consideration. \n We wish you all the very best for further improvement in your scores .\n Regards XYZ Institute Of Technology" 
                        yag = yagmail.SMTP(sender_email, "hevejrxokhqmxswp")
                        yag.send(receiver_email, subject, body)  
                        print('done')
                        student.Admission_Status='Rejected'
                        session.commit()
                        j=j+1
                else:
                    if  student.ENTRANCE_rank<=d_nm[student.Stream] :
                        x=student.Email_ID
                        sender_email = "suneha2003datta@gmail.com"
                        receiver_email = "suvadipbanerjee02@gmail.com"
                        subject = "Admission in XYZ College Update "
                        body = "Dear "+student.Name + "\n This is to inform you that your Admission in XYZ Institute Of Technology for the program "+ student.Program + " and Stream "+student.Stream+" has been accepted. \n You are requested to come to college for counselling on 15th May 2025.\n Regards XYZ Institute Of Technology" 
                        yag = yagmail.SMTP(sender_email, "hevejrxokhqmxswp")
                        yag.send(receiver_email, subject, body)  
                        print('done')
                        x=student.Email_ID
                        student.Admission_Status='Accepted'
                        session.commit()
                        j=j+1
                    else:
                        x=student.Email_ID
                        sender_email = "suneha2003datta@gmail.com"
                        receiver_email = "suvadipbanerjee02@gmail.com"
                        subject = "Admission in XYZ College Update "
                        body = "Dear "+student.Name + "\n This is to inform you that your Admission in XYZ Institute Of Technology for the program "+ student.Program + " and Stream "+student.Stream+" has been not taken under consideration. \n We wish you all the very best for further improvement in your scores .\n Regards XYZ Institute Of Technology" 
                        yag = yagmail.SMTP(sender_email, "hevejrxokhqmxswp")
                        yag.send(receiver_email, subject, body)  
                        print('done')
                        student.Admission_Status='Rejected'
                        session.commit()
                        j=j+1
        if j==0:
            return 'There is no candidate in the Stream ' + Stream +' who have given any application recently.'
        else:
            return 'All candidates under Stream '+ Stream +' have been shortlisted and have been communicated through email.'
    elif Stream == 'all':
        students = session.query(Students).filter(Students.Program==Program).all()
        for student in students:
            if student.Admission_Status=='Pending':
                if student.Stream in d_en.keys():
                    if  student.ENTRANCE_rank<=d_en[student.Stream] :
                        x=student.Email_ID
                        sender_email = "suneha2003datta@gmail.com"
                        receiver_email = "suvadipbanerjee02@gmail.com"
                        subject = "Admission in XYZ College Update "
                        body = "Dear "+student.Name + "\n This is to inform you that your Admission in XYZ Institute Of Technology for the program "+ student.Program + " and Stream "+student.Stream+" has been accepted. \n You are requested to come to college for counselling on 15th May 2025.\n Regards XYZ Institute Of Technology" 
                        yag = yagmail.SMTP(sender_email, "hevejrxokhqmxswp")
                        yag.send(receiver_email, subject, body)  
                        print('done')
                        x=student.Email_ID
                        student.Admission_Status='Accepted'
                        session.commit()
                        j=j+1
                    else:
                        x=student.Email_ID
                        sender_email = "suneha2003datta@gmail.com"
                        receiver_email = "suvadipbanerjee02@gmail.com"
                        subject = "Admission in XYZ College Update "
                        body = "Dear "+student.Name + "\n This is to inform you that your Admission in XYZ Institute Of Technology for the program "+ student.Program + " and Stream "+student.Stream+" has been not taken under consideration. \n We wish you all the very best for further improvement in your scores .\n Regards XYZ Institute Of Technology" 
                        yag = yagmail.SMTP(sender_email, "hevejrxokhqmxswp")
                        yag.send(receiver_email, subject, body)  
                        print('done')
                        student.Admission_Status='Rejected'
                        session.commit()
                        j=j+1
                else:
                    if  student.ENTRANCE_rank<=d_nm[student.Stream] :
                        x=student.Email_ID
                        sender_email = "suneha2003datta@gmail.com"
                        receiver_email = "suvadipbanerjee02@gmail.com"
                        subject = "Admission in XYZ College Update "
                        body = "Dear "+student.Name + "\n This is to inform you that your Admission in XYZ Institute Of Technology for the program "+ student.Program + " and Stream "+student.Stream+" has been accepted. \n You are requested to come to college for counselling on 15th May 2025.\n Regards XYZ Institute Of Technology" 
                        yag = yagmail.SMTP(sender_email, "hevejrxokhqmxswp")
                        yag.send(receiver_email, subject, body)  
                        print('done')
                        x=student.Email_ID
                        student.Admission_Status='Accepted'
                        session.commit()
                        j=j+1
                    else:
                        x=student.Email_ID
                        sender_email = "suneha2003datta@gmail.com"
                        receiver_email = "suvadipbanerjee02@gmail.com"
                        subject = "Admission in XYZ College Update "
                        body = "Dear "+student.Name + "\n This is to inform you that your Admission in XYZ Institute Of Technology for the program "+ student.Program + " and Stream "+student.Stream+" has been not taken under consideration. \n We wish you all the very best for further improvement in your scores .\n Regards XYZ Institute Of Technology" 
                        yag = yagmail.SMTP(sender_email, "hevejrxokhqmxswp")
                        yag.send(receiver_email, subject, body)  
                        print('done')
                        student.Admission_Status='Rejected'
                        session.commit()
                        j=j+1
        if j==0:
            return 'There is no candidate in the Program ' + Program +' who have given any application recently.'
        else:
            return 'All candidates under Program '+ Program +' have been shortlisted and have been communicated through email.'       
    else:
        students = session.query(Students).filter(Students.Stream==Stream,Students.Program==Program).all()
        for student in students:
            if student.Admission_Status=='Pending':
                if student.Stream in d_en.keys():
                    if  student.ENTRANCE_rank<=d_en[student.Stream] :
                        x=student.Email_ID
                        sender_email = "suneha2003datta@gmail.com"
                        receiver_email = "suvadipbanerjee02@gmail.com"
                        subject = "Admission in XYZ College Update "
                        body = "Dear "+student.Name + "\n This is to inform you that your Admission in XYZ Institute Of Technology for the program "+ student.Program + " and Stream "+student.Stream+" has been accepted. \n You are requested to come to college for counselling on 15th May 2025.\n Regards XYZ Institute Of Technology" 
                        yag = yagmail.SMTP(sender_email, "hevejrxokhqmxswp")
                        yag.send(receiver_email, subject, body)  
                        print('done')
                        student.Admission_Status='Accepted'
                        session.commit()
                        j=j+1
                    else:
                        x=student.Email_ID
                        sender_email = "suneha2003datta@gmail.com"
                        receiver_email = "suvadipbanerjee02@gmail.com"
                        subject = "Admission in XYZ College Update "
                        body = "Dear "+student.Name + "\n This is to inform you that your Admission in XYZ Institute Of Technology for the program "+ student.Program + " and Stream "+student.Stream+" has been not taken under consideration. \n We wish you all the very best for further improvement in your scores .\n Regards XYZ Institute Of Technology" 
                        yag = yagmail.SMTP(sender_email, "hevejrxokhqmxswp")
                        yag.send(receiver_email, subject, body)  
                        print('done')
                        student.Admission_Status='Rejected'
                        session.commit()
                        j=j+1
                else:
                    if  student.ENTRANCE_rank<=d_nm[student.Stream] :
                        x=student.Email_ID
                        sender_email = "suneha2003datta@gmail.com"
                        receiver_email = "suvadipbanerjee02@gmail.com"
                        subject = "Admission in XYZ College Update "
                        body = "Dear "+student.Name + "\n This is to inform you that your Admission in XYZ Institute Of Technology for the program "+ student.Program + " and Stream "+student.Stream+" has been accepted. \n You are requested to come to college for counselling on 15th May 2025.\n Regards XYZ Institute Of Technology" 
                        yag = yagmail.SMTP(sender_email, "hevejrxokhqmxswp")
                        yag.send(receiver_email, subject, body)  
                        print('done')
                        x=student.Email_ID
                        student.Admission_Status='Accepted'
                        session.commit()
                        j=j+1
                    else:
                        x=student.Email_ID
                        sender_email = "suneha2003datta@gmail.com"
                        receiver_email = "suvadipbanerjee02@gmail.com"
                        subject = "Admission in XYZ College Update "
                        body = "Dear "+student.Name + "\n This is to inform you that your Admission in XYZ Institute Of Technology for the program "+ student.Program + " and Stream "+student.Stream+" has been not taken under consideration. \n We wish you all the very best for further improvement in your scores .\n Regards XYZ Institute Of Technology" 
                        yag = yagmail.SMTP(sender_email, "hevejrxokhqmxswp")
                        yag.send(receiver_email, subject, body)  
                        print('done')
                        student.Admission_Status='Rejected'
                        session.commit()
                        j=j+1
        if j==0:
            return 'There is no candidate in the Stream ' + Stream +' and Program '+ Program +' who have given any application recently.'
        else:
            return 'All candidates under Stream '+ Stream +' and Program '+ Program +' have been shortlisted and have been communicated through email.'

def A4(Sid=None,Rs=None,Bnk=None,Jh=None):
    global sid
    print(Sid,Rs,Bnk)
    if not Sid:
        return "Please provide Your Student id."
    else:
        sid=Sid
    GH={"UG":1500000,"PG":2000000}
    student=session.query(Loan).filter(Loan.Student_ID==sid).first()
    ll={'ICICI':10 , 'HDFC':9.25, 'SBI':8.5, 'Bank_of_Boroda':7.5, 'Indian_overseas':9 ,'others':12}
    # em=(Rs+(Rs*ll))/24
    if Jh =='True':
        return "Please contact college office."
    if not Rs and not Bnk:
        if student:
            if student.Loan_Status == "Pending":
                if student.Admission_Proof=='Yes' and student.Id_Proof=='Yes' and student.Income_Proof=='Yes' and student.Address_Proof=='Yes':
                    student.Loan_Status=='Accepted'
                    session.commit()
                    return "Your loan request is accepted."
                else:
                    if student.Admission_Proof=='No':
                        return ' Your Admission proof that you submitted to college is not correct or you may not have provided , please seek college .'
                    if student.Address_Proof=='No':
                        return ' Your Address proof that you submitted to college is not correct or you may not have provided , please seek college .'
                    if student.Id_Proof=='No':
                        return ' Your Id proof that you submitted to college is not correct or you may not have provided , please seek college .'
                    if student.Income_Proof=='No':
                        return ' Your Income proof that you submitted to college is not correct or you may not have provided , please seek college .'
            elif student.Loan_Status == "Accepted":
                return "Your loan has already been accepted."
            else:
                return "Your loan request has been rejected."
        else:
            return "You donot seem to have applied before . Please provide your Student ID and loan amount and Bank Name."
    if not Rs or not Bnk:
        if not Rs:
            return "Please provide the loan amount (Rs)."
        if not Bnk:
            return "Please provide the bank name."
    if Sid and Rs and Bnk:
        student=session.query(Students).filter(Students.Student_ID==sid).first()
        if student :
            vb=session.query(Students).filter(Students.Student_ID==sid).first()
            if vb:
                if float(Rs) > GH[vb.Program]:
                    return "Loan amount exceeds the limit. You are not eligible for this loan."
                new=Loan(Loan_ID=11)
                new.Student_Id=sid
                new.Name= session.query(Students).filter(Students.Student_ID==sid).first().Name
                new.Phone_No=session.query(Students).filter(Students.Student_ID==sid).first().Phone_No
                new.Email_ID = session.query(Students).filter(Students.Student_ID==sid).first().Email_ID
                new.Guardian_Name =session.query(Students).filter(Students.Student_ID==sid).first().Guardian_Name
                new.Interest =Rs+(Rs*ll[Bnk])
                new.EMI= new.Interest/24
                new.Loan_Status='Pending'
                new.Rs_Granted=Rs
                new.Bank_Name=Bnk
                session.commit()
                return "Thanks for applying."
        else:
            return "Please Do your Admission first "
 

FUNCTIONS = [
    {
        "name": "A1",
        "description": "Trying to fetch general information about college cirriculum or loan structure or professors or admission procedure or college clubs. ",
        "parameters": {
            "type": "object",
            "properties": {
                "qs": {"type": "string", "description": "the question which asks information about college"}
            },
            "required": ["qs"],
        },
    },
    {
        "name": "A3",
        "description": "Asking to shortlist candidates who applied for admission",
        "parameters": {
            "type": "object",
            "properties": {
                "Program": {"type": "string", "description": "the progrsm like UG/PG only give if it's mentioned"},
                "Stream": {"type": "string", "description": "the Stream. If it's Mtech then for department Electronics & Communication Engineering  write ECE_G , if for Btech then for department Electronics & Communication Engineering write ECE_B , if MBA or BBA write MBA or BBA , if Msc in Physics write M_P and if Bsc write B_P for physics. only give if it's mentioned"},
                "var":{"type": "string", "description": "the value is always true"}

            },
            "required": ['var'],
        },
    },
    {
        "name": "A4",
        "description": "If a student gives a student id or To accept new Loan Requests or to edit previous loan requests or to seek status of already applied loan requests giving a student id",
        "parameters": {
            "type": "object",
            "properties": {
               "Sid": {"type": "integer", "description": "The student ID number mentioned by the user. Should be extracted from the user message. If not given, set to null."},
               "Rs": {"type": "integer", "description": "the Rs amount asked for loan if given else None "},
               "Bnk": {"type": "string", "description": "the Bank Name codes which includes codes like ICICI , HDFC, SBI, Bank_of_Boroda, Indian_overseas and others. if given else None"},
               "Jh": {"type": "string", "description": "it's True if it's asked to edit loan details and False if just asked for just status or new loan request"}
            },
            "required": ["Jh","Sid","Rs","Bnk"],
        },
    }
    
]

@app.post("/genova")
async def genova(promptt: str = Form(...), file: Optional[UploadFile] = File(None) ):

    promppt=json.loads(promptt)["prompt"]
    print(promppt,file)
    data = {
        "model": "gpt-4o-mini",  
        "messages": [
            {"role": "system", "content": "The user's query is given. From this query try to format the query well like a question  . Donot put any question no , just provide me the formatted query only with no other text."},
            {"role": "user", "content": promppt},
        ],
    }
    formatttedQs = requests.post("https://api.openai.com/v1/chat/completions",headers=headers,data=json.dumps(data))
    formatttedQs_json = formatttedQs.json()
    
    if "choices" in formatttedQs_json :
        qs = formatttedQs_json["choices"][0]["message"]["content"]
        print(qs)
        
    if file:
        answer= await A2(file,qs)
        return answer
    else:
        data = {
        "model": "gpt-4o-mini",
        "messages": [
            {"role": "system", "content": "You are a helpful assistant who mainly does only function calls."},
            {"role": "user", "content": qs},
        ],
        "functions": FUNCTIONS,
        "function_call": "auto",
    }
        response = requests.post("https://api.openai.com/v1/chat/completions", headers=headers, data=json.dumps(data))
        result = response.json()
        if "choices" in result and result["choices"]:
            function_call = result["choices"][0]["message"].get("function_call")
            if function_call:
                name = function_call.get("name")
                print(name)
                arguments = function_call.get("arguments")
                if arguments:
                    if isinstance(arguments, str): 
                        arguments = json.loads(arguments) 
                    funv= {
                        "name": name,
                        "arguments": dict(arguments)
                    }
                    print(type(funv["arguments"]), funv["arguments"])
                    result = globals()[funv["name"]](**funv["arguments"])
                else:
                    funv= {"name": name}
                    result = globals()[funv["name"]]()
                return json.dumps(result)
            else :
                bn=result["choices"][0]["message"].get("content")
                return json.dumps(bn+"\n Please contact the college for this detail, I am unable to provide the asked information.")
    
           

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)
    
    
    
     



