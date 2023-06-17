# -*- encoding: utf8 -*-

#　主要文件格式：　账号　-　对应黄色区域表格内容 every row became two rows in the target table
#　posting Date - 交易日期
#　Document No. - auto generated format - DA(manual):YY:MM:000X(sequence number)
# External Document - (tax file empty for now)
# Account Type - 1st row Bank Account
#                2nd row :
#                if trade amount < 0 and with payee's account number / payee's name => Vendor
#                if empty payee's account number / payee's name => G/L account
#                if trade amount > 0 => customer
# Account No. - if trade amount > 0 then payee'account number else if trade amount < 0 then debit account number
#                1st row look up in the bank file the account number for relevant code
#                2nd row look up payee's name in Vendor's file (code) if not, find in chart of accounts (code) and account type => G/L account 
# Posting Group - 1st empty for bank 
#                 2nd : payee'name -> vender posting group file, find vendor posting group (anything except presupplie) [only for vendor / customer]
# Account Name - 1st row bank file name field
#                2nd row company name in Vendor file name / coa
# Description - from account name if negative trade amount => 支付 + 2nd row account name + remark in source/付款　[CN/EN]
#                2nd row if empty payee's name => 
#                     Acc type -> G/L Acc No. 6603.01 Acc Name: 手续费　bank charge Description: 银行手续费　bank charge
# Amount - 1st row trade amount
#          2nd row - trade amount

import argparse
import pandas as pd
import csv
import datetime
import traceback

pd.set_option('display.max_columns', None)
pd.set_option('display.max_rows', None)

keyword_inquirer_acc_num = "账号"
keyword_transaction_type = "交易"
keyword_account_receivable = "来账"
keyword_account_payable = "往账"
keyword_transaction_date = "交易日期"
keyword_payee_name = "收款人名称"
keyword_payee_acc_num = "收款人账号"
keyword_payer_acc_num = "付款人账号"
keyword_remark = "交易附言"
keyword_trade_amount = "交易金额"

keyword_acc_type_vendor = "Vendor"
keyword_acc_type_customer = "Customer"
keyword_acc_type_gl = "G/L account"

keyword_target_post_date = "Posting Date"
keyword_target_document_no = "Document No."
keyword_target_external_doc_no = "External Document No."
keyword_target_acc_type = "Account Type"
keyword_target_acc_no = "Account No."
keyword_target_post_group = "Posting Group"
keyword_target_acc_name = "Account Name"
keyword_target_desc = "Description"
keyword_target_amount = "Amount"

keyword_bank_name = "Name"
keyword_bank_no = "No."

keyword_vendor_name = "Name"
keyword_vendor_no = "No."
keyword_vendor_post_group = "Vendor Posting Group"
keyword_vendor_post_group_remove = "External- Presupplie"

keyword_customer_name = "Name"
keyword_customer_no = "No."
keyword_customer_post_group = "Customer Posting Group"
keyword_customer_misc = "填对应科目 "
keyword_customer_misc_keep = "1122"

keyword_coa_name = "Name"
keyword_coa_no = "No."

now = datetime.datetime.now()
year = now.strftime("%y")
month = now.strftime("%m")

message_list = set()

def read_csv_line_by_line(file_path):
    input_data = {}
    with open(file_path, 'r', encoding='utf-8') as csv_file:
        csv_reader = csv.reader(csv_file)
        column_names = []
        account_num = ""
        data_array = []        
        for line in csv_reader:
            # Process each line of the CSV file
            # print(line)
            if keyword_inquirer_acc_num in line[0]:
                if (account_num and data_array and column_names):
                    input_data[account_num] = pd.DataFrame(data_array, columns=column_names)
                    # print("A.{0}".format(account_num))
                    data_array = []
                    column_names = []
                    account_num = ""
                account_num = line[1]
                continue
            else:
                if keyword_transaction_type in line[0]: # column name
                    column_names = [item.split('[')[0] for item in line] # remove English
                elif keyword_account_receivable in line[0] or\
                        keyword_account_payable in line[0]:
                    data_array.append(line)
                    
        if data_array and column_names:
            input_data[account_num] = pd.DataFrame(data_array, columns=column_names)
            # print("B.{0}".format(account_num))
                
    return input_data

def process_input(input_data, bank, coa, customer, vendor, target):
    target = target.iloc[0:0] # drop all target data
    for _, data in input_data.items():
        for i in range(data.shape[0]):
            data_row = data.iloc[i]
            
            # for each row we produce two new target rows
            # 1st row
            ###############################
            post_date = data_row[keyword_transaction_date]
            document_no = "DA" + year + month + str(i+1).zfill(4)
            amount = float(data_row[keyword_trade_amount].replace(',',''))
            acc_type = "Bank Account"
            
            bank_acc = data_row[keyword_payer_acc_num]\
                        if amount < 0 else data_row[keyword_payee_acc_num]
            search_bank = bank[bank[keyword_bank_name].str.contains(bank_acc)]
            if search_bank.empty:
                err_msg = "{0} not found in bank file".format(bank_acc)
                message_list.add(err_msg)
                # print(err_msg)
                acc_no = ""
                acc_name = ""
            else:
                acc_no = search_bank[keyword_bank_no].iloc[0]
                acc_name = search_bank[keyword_bank_name].iloc[0]
            post_group = ""
            desc = ""
        
            target_row = {keyword_target_post_date: post_date, 
                          keyword_target_document_no: document_no, 
                          keyword_target_external_doc_no: "",
                          keyword_target_acc_type: acc_type, 
                          keyword_target_acc_no: acc_no, 
                          keyword_target_post_group: post_group, 
                          keyword_target_acc_name: acc_name, 
                          keyword_target_desc: desc,
                          keyword_target_amount: amount}
            
            
            ########################################################
            # 2nd row ##############################################
            ##############################################
            # post_date = data_row[keyword_transaction_date] # defined above
            # document_no = "DA" + year + month + str(i+1).zfill(4) # defined above
            payee_name = data_row[keyword_payee_name]
            if payee_name:
                if amount < 0:
                    acc_type = keyword_acc_type_vendor
                else: # > 0
                    acc_type = keyword_acc_type_customer
                search_vendor = vendor[vendor[keyword_vendor_name].str.contains(payee_name)]
                search_customer = customer[customer[keyword_customer_name].str.contains(payee_name)]
                if amount < 0:
                    if search_vendor.shape[0] > 0:
                        acc_no = search_vendor[keyword_vendor_no].iloc[0]
                        acc_name = search_vendor[keyword_vendor_no].iloc[0]
                        post_group = search_vendor[keyword_vendor_post_group].iloc[0]\
                                if acc_type != keyword_acc_type_gl else ""
                    else:
                        search_coa = coa[coa[keyword_coa_name].str.contains(payee_name)]
                        if search_coa.empty:
                            err_msg = "{0} not found in coa file".format(payee_name)
                            message_list.add(err_msg)
                            # print(err_msg)
                            acc_no = ""
                            acc_name = ""
                            acc_type = ""
                        else:
                            acc_no = search_coa[keyword_coa_no].iloc[0]
                            acc_name = search_coa[keyword_coa_name].iloc[0]
                            acc_type = keyword_acc_type_gl
                else: # > 0
                    if search_customer.empty:
                        acc_no = ""
                        err_msg = "{0} not found in customer file".format(payee_name)
                        message_list.add(err_msg)
                        # print(err_msg)
                    else:
                        acc_no = search_customer[keyword_customer_no].iloc[0]
                        post_group = search_customer[keyword_customer_post_group].iloc[0]\
                                if acc_type != keyword_acc_type_gl else ""

                if amount < 0:
                    desc = "支付" + acc_name + "付款/" + data_row[keyword_remark]
                else:
                    desc = "收到" + acc_name + "付款/" + data_row[keyword_remark]
            else:
                acc_type = keyword_acc_type_gl
                acc_no = "6603.01"
                acc_name = "手续费/bank charge"
                desc = "银行手续费/bank charge"
            amount = -amount
        
            target_row2 = {keyword_target_post_date: post_date, 
                          keyword_target_document_no: document_no, 
                          keyword_target_external_doc_no: "",
                          keyword_target_acc_type: acc_type, 
                          keyword_target_acc_no: acc_no, 
                          keyword_target_post_group: post_group, 
                          keyword_target_acc_name: acc_name, 
                          keyword_target_desc: desc,
                          keyword_target_amount: amount}
            
            target_row[keyword_target_desc] = target_row2[keyword_target_desc]
            
            target = target.append(target_row, ignore_index = True)
            target = target.append(target_row2, ignore_index = True)
    return target

    

def main(input_file, bank_file, coa_file, customer_file, vendor_file, target_file):
    # Read the input file into a pandas dataframe
    input_data = read_csv_line_by_line(input_file)
    
    # Read the three source files into pandas dataframes
    df_bank = pd.read_csv(bank_file, encoding='utf-8')
    df_coa = pd.read_csv(coa_file, encoding='utf-8')
    df_customer = pd.read_csv(customer_file, encoding='utf-8')
    df_vendor = pd.read_csv(vendor_file, encoding='utf-8')
    
    # clean bank data
    df_bank = df_bank.iloc[1:]
    df_bank = df_bank.rename(columns=df_bank.iloc[0]).drop(df_bank.index[0])
    df_bank = df_bank.dropna(subset=[keyword_bank_no])
    # print(df_bank)
    df_coa = df_coa.dropna(subset=[keyword_coa_no])
    # print(df_coa)
    df_customer = df_customer.iloc[1:]
    df_customer = df_customer.rename(columns=df_customer.iloc[0]).drop(df_customer.index[0])
    df_customer = df_customer[df_customer[keyword_customer_misc] == keyword_customer_misc_keep]
    df_customer = df_customer.dropna(subset=[keyword_customer_no])
    
    # clean vendor data
    df_vendor = df_vendor.iloc[1:]
    df_vendor = df_vendor.rename(columns=df_vendor.iloc[0]).drop(df_vendor.index[0])
    df_vendor = df_vendor[df_vendor[keyword_vendor_post_group] != keyword_vendor_post_group_remove]
    df_vendor = df_vendor.dropna(subset=[keyword_vendor_no])
    # print(df_vendor)
    
    # Read the target format
    df_target = pd.read_csv(target_file, encoding='utf-8')
    
    # Perform operations with the dataframes
    try:
        df_target = process_input(input_data, 
                                   df_bank,
                                   df_coa,
                                   df_customer,
                                   df_vendor, 
                                   df_target)
        df_target.to_csv('output.csv', encoding='utf-8', index=False) #, 
    except Exception as e:
        traceback.print_exc()
    print(df_target.shape)
    [print(m) for m in message_list]


if __name__ == '__main__':
    # Create an argument parser
    parser = argparse.ArgumentParser(description='Process CSV files and merge them.')
    
    # Add the command line arguments
    parser.add_argument('-i', '--input', help='Input file')
    parser.add_argument('-b', '--bank', help='Bank file')
    parser.add_argument('-c', '--coa', help='COA file')
    parser.add_argument('-u', '--customer', help='Customer file')
    parser.add_argument('-v', '--vendor', help='Vendor file')
    parser.add_argument('-t', '--target', help='Target file')
    
    # Parse the command line arguments
    args = parser.parse_args()
    
    # Call the main function with the provided arguments
    main(args.input, args.bank, args.coa, args.customer, args.vendor, args.target)