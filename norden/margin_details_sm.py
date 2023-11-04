from datetime import datetime
from lib2to3.pytree import convert
import frappe
import erpnext
from frappe.utils import date_diff, add_months, today, add_days, nowdate,formatdate,flt
from frappe.utils.csvutils import read_csv_content
from frappe.utils.file_manager import get_file
import json
from forex_python.converter import CurrencyRates
from frappe.model.document import Document
import pandas as pd
from frappe.model.rename_doc import rename_doc
from frappe.model.naming import make_autoname
from erpnext.setup.utils import get_exchange_rate


@frappe.whitelist()
def margin(item_details,company,currency,margin_currency,exchange_rate,user,price_list,territory,line_item_addition,line_item_discount,footer_discount):
    item_details = json.loads(item_details)
    data = ''
    if "CFO" in frappe.get_roles(frappe.session.user) or "COO" in frappe.get_roles(frappe.session.user) or "HOD" in frappe.get_roles(frappe.session.user) or "Accounts User" in frappe.get_roles(frappe.session.user):
        data+= '<table ><style>td { text-align:left } table,tr,td { padding:5px;border: 1px solid black; font-size:11px;} </style>'
        data+='<tr><th  colspan=13 style="padding:1px;font-size:14px;background-color:#e20026;color:white;"><center><b>MARGIN BY VALUE & MARGIN BY PERCENTAGE</b></center></th></tr>'
        spl = 0
        for i in item_details:
            if i["special_cost"] > 0:
                spl = spl + 1
        if spl == 0:
            data+='<tr style="background-color:lightgrey"><td width="150px"><b>ITEM</b></td><td width="400px;"><b>ITEM NAME</b></td><td><b>QTY</b></td>'
            if price_list in ["Singapore Internal Cost","Bangladesh Internal Cost","Srilanka Internal Cost","Cambodia Internal Cost","Vietnam Internal Cost","Indonesia Internal Cost","Malaysia Internal Cost","Philippines Internal Cost"]:
                data+='<td><b>INTERNAL COST</b></td><td><b>INTERNAL COST %</b></td>'
            if price_list in ["Singapore Freight","Bangladesh Freight","Srilanka Freight","Cambodia Freight","Vietnam Freight","Indonesia Freight","Malaysia Freight","Philippines Freight"]:
                data+='<td><b>FREIGHT</b></td><td><b>FREIGHT %</b></td>'
            if price_list in ["Singapore Sales Price","Bangladesh Sales Price","Srilanka Sales Price","Cambodia Sales Price","Vietnam Sales Price","Indonesia Sales Price","Malaysia Sales Price","Philippines Sales Price"]:
                data+='<td><b>SALES PRICE</b></td><td><b>SALES PRICE %</b></td>'
            

            if price_list == "UK Freight":
                data+='<td><b>FREIGHT</b></td><td><b>FREIGHT %</b></td>'
            if price_list == "UK Destination Charges":
                data+='<td><b>DESTINATION CHARGES</b></td><td><b>DESTINATION CHARGES %</b></td>'
            if price_list == "UK Installer":
                data+='<td><b>INSTALLER</b></td><td><b>INSTALLER %</b></td>'
            if price_list == "UK Distributor":
                data+='<td><b>DISTRIBUTOR</b></td><td><b>DISTRIBUTOR %</b></td>'
           
            if price_list == "Landing - NCMEF":
                data+='<td><b>LANDING</b></td><td><b>LANDING %</b></td>'
            if price_list == "Internal - NCMEF":
                data+='<td><b>INTERNAL</b></td><td><b>INTERNAL %</b></td>'
            if price_list == "Incentive - NCMEF":
                data+='<td><b>INCENTIVE</b></td><td><b>INCENTIVE %</b></td>'
            if price_list == "Dist. Price - NCMEF":
                data+='<td><b>DISTRIBUTOR</b></td><td><b>DISTRIBUTOR %</b></td>'
            if price_list == "Saudi Dist. - NCMEF":
                data+='<td><b>SAUDI</b></td><td><b>SAUDI %</b></td>'
            if price_list == "Project Group - NCMEF":
                data+='<td><b>PROJECT</b></td><td><b>PROJECT %</b></td>'
            if price_list == "Retail - NCMEF":
                data+='<td><b>RETAIL</b></td><td><b>RETAIL %</b></td>'
            if price_list == "Electra Qatar - NCMEF":
                data+='<td><b>ELECTRA</b></td><td><b>ELECTRA %</b></td>'

            
            if price_list == "India Landing":
                data+='<td><b>LANDING</b></td><td><b>LANDING%</b></td>'
            if price_list == "India SPC":
                data+='<td><b>SPC</b></td><td><b>SPC%</b></td>'
            if price_list == "India STP":
                data+='<td><b>STP</b></td><td><b>STP%</b></td>'
            if price_list == "India LTP":
                data+='<td><b>LTP</b></td><td><b>LTP%</b></td>'
            if price_list == "India DTP":
                data+='<td><b>DTP</b></td><td><b>DTP%</b></td>'
            if price_list == "India MOP":
                data+='<td><b>MOP</b></td><td><b>MOP%</b></td>'
            if price_list == "India MRP":
                data+='<td><b>MRP</b></td><td><b>MRP%</b></td>'
            data += '<td><b>SP</b></td></tr>'
        else:
            data+='<tr><td><b>ITEM</b></td><td><b>ITEM NAME</b></td><td><b>STOCK</b></td><td><b>PO</b></td><td><b>TOTAL</b></td><td><b>QTY</b></td><td><b>COST</b></td><td><b>COST %</b></td></td><td><b>INTERNAL COST</b></td><td><b>INTERNAL COST %</b></td><td><b>SPECIAL PRICE</b></td><td><b>SELLING PRICE</b></td></tr>'

    total_selling_price = 0
    spcl = 0
    dubai_landing_margin = 0
    dubai_incentive_margin = 0
    dubai_internal_margin = 0
    dubai_distributor_margin = 0
    saudi_margin = 0
    dubai_project_margin = 0
    dubai_retail_margin = 0
    dubai_electra_margin = 0
    d_sbu_margin = 0
    india_landing_margin = 0
    india_spc_margin = 0
    india_ltp_margin = 0
    india_dtp_margin = 0
    india_stp_margin = 0 
    india_mop_margin = 0
    india_mrp_margin = 0
    total_selling_price = 0

    internal_cost_total = 0
    internal_cost_total_margin = 0 
    sales_price_total = 0
    sales_price_total_margin = 0
    freight_total = 0
    freight_total_margin = 0

    uk_freight_margin= 0
    uk_destination_charges_margin = 0
    uk_installer_margin = 0
    uk_distributor_margin = 0

    uk_freight_total= 0
    uk_freight_total_margin= 0
    uk_destination_charges_total = 0
    uk_destination_charges_total_margin= 0
    uk_installer_total = 0
    uk_installer_total_margin = 0
    uk_distributor_total = 0
    uk_distributor_total_margin = 0

    dubai_landing_total = 0
    dubai_landing_total_margin = 0
    dubai_incentive_total = 0
    dubai_incentive_total_margin = 0
    dubai_internal_total = 0
    dubai_internal_margin = 0
    dubai_distributor_total = 0
    dubai_distributor_margin = 0
    saudi_total = 0
    saudi_total_margin = 0
    dubai_project_total = 0
    dubai_project_total_margin = 0
    dubai_retail_total = 0
    dubai_retail_total_margin = 0
    dubai_electra_total = 0
    dubai_electra_total_margin = 0


    india_landing_total = 0
    india_landing_total_margin = 0
    india_spc_total = 0
    india_spc_total_margin = 0
    india_ltp_total = 0
    india_ltp_total_margin = 0
    india_dtp_total = 0
    india_dtp_total_margin = 0
    india_stp_total = 0 
    india_stp_total_margin = 0 
    india_mop_total = 0
    india_mop_total_margin = 0
    india_mrp_total = 0
    india_mrp_total_margin = 0

    sbu_total = 0
    sbu_total_margin = 0
    total_cost = 0

    for i in item_details:
        total_selling_price = round((total_selling_price + i["amount"]),2)
        country = frappe.get_value("Company",{"name":company},["country"])
        amount = i["amount"]
        if i["special_cost"] > 0:
            spcl = spcl + 1

        sbu = frappe.get_value("Item Price",{'item_code':i["item_code"],'price_list':'STANDARD BUYING-USD'},["price_list_rate"])
        # sbu_total = sbu_total + sbu
        if not sbu:
            sbu = 0
        ep = get_exchange_rate("USD",margin_currency)    
        sbu = round(sbu*ep,1)
        # amount = round(amount*ep,1)
        sbus = round((sbu * i["qty"]),2)
        sbu_total = round((sbus + sbu_total),2)
        sbu_margin = round(((amount- sbu*i["qty"])/amount*100),2)
        sbu_total_margin = round(((amount - sbu_total)/amount*100),2)

        if territory == "United Kingdom":
            uk_table = frappe.get_single("Margin Price Tool").uk
            item_group = frappe.get_value("Item",{"name":i["item_code"]},["item_sub_group"])
            for s in uk_table:
                if item_group == s.item_group:
                    uk_freight = round((sbu * s.freight),2)*i["qty"]
                    uk_destination_charges = round((uk_freight * s.destination_charges),2)*i["qty"]
                    uk_installer = round((uk_destination_charges/(100 - s.installer)*100),2)
                    uk_distributor = round((uk_installer/(100 - s.distributor)*100),2)
                    uk_freight_margin = (((amount - uk_freight)/amount)*100)
                    uk_destination_charges_margin = (((amount - uk_destination_charges)/amount)*100)
                    uk_installer_margin = (((amount -  uk_installer)/amount)*100)
                    uk_distributor_margin = (((amount - uk_distributor)/amount)*100)
                    uk_freight_total =  uk_freight + uk_freight_total 
                    uk_freight_total_margin= round(((total_selling_price - uk_freight_total)/total_selling_price*100),2)
                    uk_destination_charges_total = uk_destination_charges + uk_destination_charges_total
                    uk_destination_charges_total_margin= round(((total_selling_price - uk_destination_charges_total)/total_selling_price*100),2)
                    uk_installer_total = uk_installer + uk_installer_total
                    uk_installer_total_margin = round(((total_selling_price - uk_installer_total)/total_selling_price*100),2)
                    uk_distributor_total = uk_distributor + uk_distributor_total
                    uk_distributor_total_margin = round(((total_selling_price - uk_distributor_total)/total_selling_price*100),2)

        if territory == "Dubai" or territory == "United Arab Emirates":
            exc_rate = get_exchange_rate("AED",margin_currency)
            if price_list == "Landing - NCMEF":
                dubai_landing = (frappe.get_value("Item Price",{'item_code':i["item_code"],'price_list':"Landing - NCMEF"},['price_list_rate'])*i["qty"])
                dubai_landing_total += dubai_landing * exc_rate
                dubai_landing_margin = round((((amount - dubai_landing)/amount)*100),2)
                dubai_landing_total_margin = round(((total_selling_price - dubai_landing_total)/total_selling_price*100),2)

            if price_list == "Internal - NCMEF":
                dubai_internal = (frappe.get_value("Item Price",{'item_code':i["item_code"],'price_list':"Internal - NCMEF"},['price_list_rate'])*i['qty'])
                dubai_internal_total += dubai_internal * exc_rate
                dubai_internal_margin = round((((amount - dubai_internal)/amount)*100),2)
                dubai_internal_total_margin = round(((total_selling_price - dubai_internal_total)/total_selling_price*100),2)

            if price_list == "Incentive - NCMEF":
                dubai_incentive = (frappe.get_value("Item Price",{'item_code':i["item_code"],'price_list':"Incentive - NCMEF"},['price_list_rate'])*i['qty'])
                dubai_incentive_total += dubai_incentive * exc_rate
                dubai_incentive_margin = round((((amount - dubai_incentive)/amount)*100),2)
                dubai_incentive_total_margin = round(((total_selling_price - dubai_incentive_total)/total_selling_price*100),2)

            if price_list == "Dist. Price - NCMEF":
                dubai_distributor = frappe.get_value("Item Price",{'item_code':i["item_code"],'price_list':"Dist. Price - NCMEF"},['price_list_rate'])*i['qty']
                dubai_distributor_total += dubai_distributor * exc_rate
                dubai_distributor_margin = round((((amount - dubai_distributor)/amount)*100),2)
                dubai_distributor_total_margin = round(((total_selling_price - dubai_distributor_total)/total_selling_price*100),2)

            if price_list == "Saudi Dist. - NCMEF":
                saudi = frappe.get_value("Item Price",{'item_code':i["item_code"],'price_list':"Saudi Dist. - NCMEF"},['price_list_rate'])*i['qty']
                saudi_total += saudi * exc_rate
                saudi_margin = round((((amount - saudi)/amount)*100),2)
                saudi_total_margin = round(((total_selling_price - saudi_total)/total_selling_price*100),2)

            if price_list == "Project Group - NCMEF":
                dubai_project = frappe.get_value("Item Price",{'item_code':i["item_code"],'price_list':"Project Group - NCMEF"},['price_list_rate'])*i['qty']
                dubai_project_total += dubai_project * exc_rate
                dubai_project_margin = round((((amount - dubai_project)/amount)*100),2)
                dubai_project_total_margin = round(((total_selling_price - dubai_project_total)/total_selling_price*100),2)

            if price_list == "Retail - NCMEF":
                dubai_retail = frappe.get_value("Item Price",{'item_code':i["item_code"],'price_list':"Retail - NCMEF"},['price_list_rate'])*i["qty"]
                dubai_retail_total += dubai_retail * exc_rate
                dubai_retail_margin = round((((amount - dubai_retail)/amount)*100),2)
                dubai_retail_total_margin = round(((total_selling_price - dubai_retail_total)/total_selling_price*100),2)

            if price_list == "Electra Qatar - NCMEF":
                dubai_electra = frappe.get_value("Item Price",{'item_code':i["item_code"],'price_list':"Electra Qatar - NCMEF"},['price_list_rate'])
                dubai_electra_total += dubai_electra * exc_rate
                dubai_electra_margin = round((((amount - dubai_electra)/amount)*100),2)
                dubai_electra_total_margin = round(((total_selling_price - dubai_electra_total)/total_selling_price*100),2)
            
        if territory == "India":
            india_table = frappe.get_single("Margin Price Tool").india
            item_group = frappe.get_value("Item",{"name":i["item_code"]},["item_sub_group"])
            for d in india_table: 
                if item_group == d.item_group:
                    india_landing = round((sbu * d.landing),2)*i["qty"]
                    india_spc  = round((india_landing/ d.spc),2)
                    india_ltp = round((india_spc / d.ltp),2)
                    india_dtp = round((india_ltp / d.dtp),2)
                    india_stp = round((india_dtp / d.stp),2)
                    india_mop = round((india_stp / d.mop),2)
                    india_mrp = round((india_mop / d.mrp),2)

                    india_landing_margin = (((amount - india_landing)/amount)*100)
                    india_spc_margin = (((amount - india_landing)/amount)*100)
                    india_ltp_margin = (((amount - india_ltp)/amount)*100)
                    india_dtp_margin = (((amount - india_dtp)/amount)*100)
                    india_stp_margin = (((amount - india_stp)/amount)*100) 
                    india_mop_margin = (((amount - india_mop)/amount)*100)
                    india_mrp_margin = (((amount - india_mrp)/amount)*100)  

                    india_landing_total = india_landing_total + india_landing
                    india_landing_total_margin = round(((total_selling_price - india_landing_total)/total_selling_price*100),2)
                    
                    india_spc_total =  india_spc_total +india_spc
                    india_spc_total_margin = round(((total_selling_price -  india_spc_total)/total_selling_price*100),2)
                    
                    india_ltp_total =  india_ltp_total + india_ltp
                    india_ltp_total_margin = round(((total_selling_price -  india_ltp_total)/total_selling_price*100),2)
                    
                    india_dtp_total =  india_dtp_total + india_dtp
                    india_dtp_total_margin = round(((total_selling_price -  india_dtp_total )/total_selling_price*100),2)
                    
                    india_stp_total = india_stp_total + india_stp
                    india_stp_total_margin = round(((total_selling_price -  india_stp_total)/total_selling_price*100),2)
                    
                    india_mop_total = india_mop_total + india_mop
                    india_mop_total_margin = round(((total_selling_price - india_mop_total)/total_selling_price*100),2)
                    
                    india_mrp_total = india_mrp_total +  india_mrp
                    india_mrp_total_margin = round(((total_selling_price - india_mrp_total)/total_selling_price*100),2) 

        if territory in ["Singapore","Vietnam","Philippines","Malaysia","Indonesia","Cambodia","Srilanka","Bangladesh"]:
            if territory == "Singapore":
                margin_table = frappe.get_single("Margin Price Tool").singapore
            if territory == "Vietnam":
                margin_table = frappe.get_single("Margin Price Tool").vietnam
            if territory == "Philippines":
                margin_table = frappe.get_single("Margin Price Tool").philippines
            if territory == "Malaysia":
                margin_table = frappe.get_single("Margin Price Tool").malaysia
            if territory == "Indonesia":
                margin_table = frappe.get_single("Margin Price Tool").indonesia
            if territory == "Cambodia":
                margin_table = frappe.get_single("Margin Price Tool").cambodia
            if territory == "Srilanka" or territory == "Sri Lanka":
                margin_table = frappe.get_single("Margin Price Tool").srilanka
            if territory == "Bangladesh":
                margin_table = frappe.get_single("Margin Price Tool").bangladesh
            item_group = frappe.get_value("Item",{"name":i["item_code"]},["item_sub_group"])
            for s in margin_table:
                if item_group == s.item_group:
                    ic = ((sbu * s.internal_cost))
                    internal_cost = ic*i["qty"]
                    sales_price = (((ic/(100 - s.sales_price))*100)* s.freight)*i["qty"]
                    freight = ((((ic/(100 - s.sales_price))*100)* s.freight)*i["qty"])
                    internal_cost_margin = (((amount - internal_cost)/amount)*100)
                    sales_price_margin = (((amount - sales_price)/amount)*100)
                    freight_margin = (((amount - freight)/amount)*100)
                    internal_cost_total = internal_cost + internal_cost_total
                    internal_cost_total_margin = round(((total_selling_price - internal_cost_total)/total_selling_price*100),2)
                    sales_price_total = sales_price + sales_price_total 
                    sales_price_total_margin = round(((total_selling_price - sales_price_total)/total_selling_price*100),2)
                    freight_total = freight + freight_total 
                    freight_total_margin = round(((total_selling_price - freight_total)/total_selling_price*100),2)                
       
        if "CFO" in frappe.get_roles(frappe.session.user) or "COO" in frappe.get_roles(frappe.session.user) or "HOD" in frappe.get_roles(frappe.session.user) or "Accounts User" in frappe.get_roles(frappe.session.user):
            if i["special_cost"] > 0:
                data+='<tr><td  align = "right" >%s</td><td  align = "right" >%s</td><td  align = "right" >%s</td><td  align = "right" >%s</td><td  align = "right" >%s</td><td  align = "right" >%s</td><td  align = "right" >%s</td><td  align = "right" >%s</td><td  align = "right" >%s</td><td  align = "right" >%s</td><td  align = "right" >%s</td><td  align = "right" >%s</td></tr>'%(i["item_code"],i["description"],'','','','','')
            else:
                data+='<tr><td  align = "right" >%s</td><td  align = "right" >%s</td><td  align = "right" >%s</td><'%(i["item_code"],i["description"],i["qty"])
                if price_list in ["Singapore Internal Cost","Bangladesh Internal Cost","Srilanka Internal Cost","Cambodia Internal Cost","Vietnam Internal Cost","Indonesia Internal Cost","Malaysia Internal Cost","Philippines Internal Cost"]:
                    data+='<td align = "right" >%s</td><td  align = "right" >%s</td>'%(round(internal_cost,2),round(internal_cost_margin,2))
                if price_list in ["Singapore Sales Price","Bangladesh Sales Price","Srilanka Sales Price","Cambodia Sales Price","Vietnam Sales Price","Indonesia Sales Price","Malaysia Sales Price","Philippines Sales Price"]:
                    data+='<td align = "right" >%s</td><td  align = "right" >%s</td>'%(round(sales_price,2),round(sales_price_margin,2))
                if price_list in ["Singapore Freight","Bangladesh Freight","Srilanka Freight","Cambodia Freight","Vietnam Freight","Indonesia Freight","Malaysia Freight","Philippines Freight"]:
                    data+='<td align = "right" >%s</td><td  align = "right" >%s</td>'%(round(freight,2),round(freight_margin,2))
                                
                # UK Margin 

                if price_list == "UK Freight":
                    data+='<td  align = "right" >%s</td><td  align = "right" >%s</td>'%(round(uk_freight,2),round(uk_freight_margin,2))
                if price_list ==  "UK Destination Charges":
                    data+='<td  align = "right" >%s</td><td  align = "right" >%s</td>'%(round(uk_destination_charges,2),round(uk_destination_charges_margin,2))
                if price_list == "UK Installer":
                    data+='<td  align = "right" >%s</td><td  align = "right" >%s</td>'%(round(uk_installer,2),round(uk_installer_margin,2))
                if price_list == "UK Distributor":
                    data+='<td  align = "right" >%s</td><td  align = "right" >%s</td>'%(round(uk_distributor,2),round(uk_distributor_margin,2))
                    
                # UAE Margin   
                
                if price_list == "Landing - NCMEF":
                    data+='<td  align = "right" >%s</td><td  align = "right" >%s</td>'%(round(dubai_landing,2),round(dubai_landing_margin,2))
                if price_list == "Internal - NCMEF":
                    data+='<td  align = "right" >%s</td><td  align = "right" >%s</td>'%(round((dubai_internal),2),round(dubai_internal_margin,2))
                if price_list == "Incentive - NCMEF":
                    data+='<td  align = "right" >%s</td><td  align = "right" >%s</td>'%(round(dubai_incentive,2),round(dubai_incentive_margin,2))
                if price_list == "Dist. Price - NCMEF":
                    data+='<td  align = "right" >%s</td><td  align = "right" >%s</td>'%(round(dubai_distributor,2),round(dubai_distributor_margin,2))
                if price_list == "Saudi Dist. - NCMEF":
                    data+='<td  align = "right" >%s</td><td  align = "right" >%s</td>'%(round(saudi,2),round(saudi_margin,2))
                if price_list == "Project Group - NCMEF":
                    data+='<td  align = "right" >%s</td><td  align = "right" >%s</td>'%(round(dubai_project,2),round(dubai_project_margin,2))
                if price_list == "Retail - NCMEF":
                    data+='<td  align = "right" >%s</td><td  align = "right" >%s</td>'%(round(dubai_retail,2),round(dubai_retail_margin,2))
                if price_list == "Electra Qatar - NCMEF":
                    data+='<td  align = "right" >%s</td><td  align = "right" >%s</td>'%(round(dubai_electra,2),round(dubai_electra_margin,2)) 

                if price_list == "India Landing":
                    data+='<td  align = "right" >%s</td><td  align = "right" >%s</td>'%(round(india_landing*i["qty"],2),round(india_landing_margin,2))
                if price_list == "India LTP":
                    data+='<td  align = "right" >%s</td><td  align = "right" >%s</td>'%(round(india_ltp*i["qty"],2),round(india_ltp_margin,2))
                if price_list == "India SPC":
                    data+='<td  align = "right" >%s</td><td  align = "right" >%s</td>'%(round(india_spc*i["qty"],2),round(india_spc_margin,2))
                if price_list == "India DTP":
                    data+='<td  align = "right" >%s</td><td  align = "right" >%s</td>'%(round(india_dtp*i["qty"],2),round(india_dtp_margin,2))
                if price_list == "India STP":
                    data+='<td  align = "right" >%s</td><td  align = "right" >%s</td>'%(round(india_stp*i["qty"],2),round(india_stp_margin,2))
                if price_list == "India MOP":
                    data+='<td  align = "right" >%s</td><td  align = "right" >%s</td>'%(round(india_mop*i["qty"],2),round(india_mop_margin,2))
                if price_list == "India MRP":
                    data+='<td  align = "right" >%s</td><td  align = "right" >%s</td>'%(round(india_mrp*i["qty"],2),round(india_mrp_margin,2))
                data += '<td align="right">%s</td></tr>' % (round(i['amount'],2))
   
    sbu_total_margin = round(((total_selling_price - sbu_total)/total_selling_price*100),2)
    data_1 = ''
    if "CFO" in frappe.get_roles(frappe.session.user) or "COO" in frappe.get_roles(frappe.session.user) or "HOD" in frappe.get_roles(frappe.session.user) or "Accounts User" in frappe.get_roles(frappe.session.user):
        if spcl == 0:
            data += '<tr><th><b>TOTAL MARGIN </b></th><td  align = "right" ><b>%s<b></td><td align = "right"><b>%s</b></td>'%('','')            
            if price_list in ["Singapore Internal Cost","Bangladesh Internal Cost","Srilanka Internal Cost","Cambodia Internal Cost","Vietnam Internal Cost","Indonesia Internal Cost","Malaysia Internal Cost","Philippines Internal Cost"]:
                data += '<td  align = "right" ><b>%s</b></td><td  align = "right" ><b>%s</b></td>'%(round(internal_cost_total,2),internal_cost_total_margin)
            if price_list in ["Singapore Sales Price","Bangladesh Sales Price","Srilanka Sales Price","Cambodia Sales Price","Vietnam Sales Price","Indonesia Sales Price","Malaysia Sales Price","Philippines Sales Price"]:
                data += '<td  align = "right" ><b>%s</b></td><td  align = "right" ><b>%s</b></td>'%(round(sales_price_total,2),sales_price_total_margin)       
            if price_list in ["Singapore Freight","Bangladesh Freight","Srilanka Freight","Cambodia Freight","Vietnam Freight","Indonesia Freight","Malaysia Freight","Philippines Freight"]:
                data += '<td  align = "right" ><b>%s</b></td><td  align = "right" ><b>%s</b></td>'%(round(freight_total,2),freight_total_margin)
            

            if price_list == "UK Freight":
                data += '<td  align = "right" ><b>%s</b></td><td  align = "right" ><b>%s</b></td>'%(round(uk_freight_total,2),uk_freight_total_margin)
            if price_list == "UK Destination Charges":
                data += '<td  align = "right" ><b>%s</b></td><td  align = "right" ><b>%s</b></td>'%(round(uk_destination_charges_total,2),uk_destination_charges_total_margin)       
            if price_list == "UK Installer":
                data += '<td  align = "right" ><b>%s</b></td><td  align = "right" ><b>%s</b></td>'%(round(uk_installer_total,2),uk_installer_total_margin)
            if price_list == "UK Distributor":
                data += '<td  align = "right" ><b>%s</b></td><td  align = "right" ><b>%s</b></td>'%(round(uk_distributor_total,2),uk_distributor_total_margin)
                
            if price_list == "India Landing":
                data +=  '<td  align = "right" ><b>%s</b></td><td  align = "right" ><b>%s</b></td>'%(round(india_landing_total,2),india_landing_total_margin)
            if price_list == "India LTP":
                data += '<td  align = "right" ><b>%s</b></td><td  align = "right" ><b>%s</b></td>'%(round(india_ltp_total,2),india_ltp_total_margin)       
            if price_list == "India SPC":
                data += '<td  align = "right" ><b>%s</b></td><td  align = "right" ><b>%s</b></td>' %(round(india_spc_total,2),india_spc_total_margin)
            if price_list == "India DTP":
                data += '<td  align = "right" ><b>%s</b></td><td  align = "right" ><b>%s</b></td>'%(round(india_dtp_total,2),india_dtp_total_margin)
            if price_list == "India STP":
                data += '<td  align = "right" ><b>%s</b></td><td  align = "right" ><b>%s</b></td>'%(round(india_stp_total,2),india_stp_total_margin)       
            if price_list == "India MOP":
                data += '<td  align = "right" ><b>%s</b></td><td  align = "right" ><b>%s</b></td>'%(round(india_mop_total,2),india_mop_total_margin,)
            if price_list == "India MRP":
                data += '<td  align = "right" ><b>%s</b></td><td  align = "right" ><b>%s</b></td>'%(round(india_mrp_total,2),india_mrp_total_margin,)


            
            if price_list == "Landing - NCMEF":
                data += '<td  align = "right" ><b>%s</b></td><td  align = "right" ><b>%s</b></td>'%(round(dubai_landing_total,2),dubai_landing_total_margin)
            if price_list == "Internal - NCMEF":
                data += '<td  align = "right" ><b>%s</b></td><td  align = "right" ><b>%s</b></td>'%(round(dubai_internal_total,2),dubai_internal_total_margin)      
            if price_list == "Incentive - NCMEF":
                data += '<td  align = "right" ><b>%s</b></td><td  align = "right" ><b>%s</b></td>'%(round(dubai_incentive_total,2),dubai_incentive_total_margin)
            if price_list == "Dist. Price - NCMEF":
                data += '<td  align = "right" ><b>%s</b></td><td  align = "right" ><b>%s</b></td>'%(round(dubai_distributor_total,2),dubai_distributor_total_margin)
            if price_list == "Saudi Dist. - NCMEF":
                data += '<td  align = "right" ><b>%s</b></td><td  align = "right" ><b>%s</b></td>'%(round(saudi_total,2),saudi_total_margin)       
            if price_list == "Project Group - NCMEF":
                data += '<td  align = "right" ><b>%s</b></td><td  align = "right" ><b>%s</b></td>'%(round(dubai_project_total,2),dubai_project_total_margin)
            if price_list == "Retail - NCMEF":
                data += '<td  align = "right" ><b>%s</b></td><td  align = "right" ><b>%s</b></td>'%(round(dubai_retail_total,2),dubai_retail_total_margin)
            if price_list == "Electra Qatar - NCMEF":
                data += '<td  align = "right" ><b>%s</b></td><td  align = "right" ><b>%s</b></td>'%(round(dubai_electra_total,2),dubai_electra_total_margin)
            data += '<td align="right">%s</td>' % (round(total_selling_price,2))
            data_1 = '<table border=1 style="width:60%"><tr><th  colspan=13 style="padding:1px;font-size:14px;background-color:#e20026;color:white;"><center><b>MARGIN SUMMARY</b></center></th></tr>'
            data_1 += '<tr><td style="font-weight:bold;background-color:#dce0e3;font-size:12px">Total Cost Price</td><td style="font-weight:bold;font-size:12px;">%s</td><td style="font-weight:bold;background-color:#dce0e3;font-size:12px">Total Selling Price</td><td style="font-weight:bold;font-size:12px;">%s</td></tr>' %(sbu_total,round((total_selling_price + flt(line_item_discount)) - flt(line_item_addition),2))
            data_1 += '<tr><td style="font-weight:bold;background-color:#dce0e3;font-size:12px">Line Item Addition</td><td style="font-weight:bold;font-size:12px;">%s</td><td style="font-weight:bold;background-color:#dce0e3;font-size:12px">Line Item Discount</td><td style="font-weight:bold;font-size:12px;">%s</td></tr>' %(line_item_addition,line_item_discount)
            data_1 += '<tr><td style="font-weight:bold;background-color:#dce0e3;font-size:12px">Footer Discount</td><td style="font-weight:bold;font-size:12px;">%s</td><td style="font-weight:bold;background-color:#dce0e3;font-size:12px">Net Sales Amount</td><td style="font-weight:bold;font-size:12px;">%s</td></tr>' %(footer_discount,total_selling_price)
            data_1 += '<tr><td style="font-weight:bold;background-color:#dce0e3;font-size:12px"></td><td></td><td style="font-weight:bold;background-color:#dce0e3;font-size:12px">Sales Profit</td><td style="font-weight:bold;font-size:12px;">%s</td></tr>' %(round((total_selling_price - sbu_total),2))
            data_1 += '<tr><td style="font-weight:bold;background-color:#dce0e3;font-size:12px"></td><td></td><td style="font-weight:bold;background-color:#dce0e3;font-size:12px">Profit %%</td><td style="font-weight:bold;font-size:12px;">%s %%</td></tr>' %(round(((total_selling_price - sbu_total)/total_selling_price*100),2))
            data_1 += '</table>'
        else:
            data += '<tr><th><b>TOTAL MARGIN</b></th><td  align = "right" ><b>%s<b></td><td  align = "right" ><b>%s</b></td><td  align = "right" ><b>%s</b><td  align = "right" ><b>%s</b></td><td  align = "right" ><b>%s</b></td><td  align = "right" ><b>%s</b></td><td  align = "right" ><b>%s</b></td></tr>'%(price_list,'','','','','')
   
    data+='</table>'
    return data_1,data
