// WMIClient.cpp : This file contains the 'main' function. Program execution begins and ends there.
//
/*
BSD 3-Clause License

Copyright (c) 2017, SafeBreach Labs
All rights reserved.

Redistribution and use in source and binary forms, with or without
modification, are permitted provided that the following conditions are met:

* Redistributions of source code must retain the above copyright notice, this
  list of conditions and the following disclaimer.

* Redistributions in binary form must reproduce the above copyright notice,
  this list of conditions and the following disclaimer in the documentation
  and/or other materials provided with the distribution.

* Neither the name of the copyright holder nor the names of its
  contributors may be used to endorse or promote products derived from
  this software without specific prior written permission.

THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE
FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL
DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR
SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER
CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY,
OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
*/


#include "pch.h"
#include "WMIClient.h"

using namespace std;

int main()
{
    cout << "Hello World!\n";
	//CreateClass(L"root\\cimv2", L"Win32_Azouri");
	wchar_t ns[] = L"root\\cimv2";
	wchar_t cn[] = L"Win32_Azouri";
	CreateClass(ns, cn);
	/*wstring* ns = new wstring(L"root\\cimv2");
	wstring* cn = new wstring(L"Win32_Azouri");
	CreateClass(ns, cn);*/
	wchar_t prop[] = L"Caption";
	wchar_t val[] = L"AAAAA";
	CreateProperty(ns, cn, prop, val);
	
	//DeleteProperty(ns, cn, prop);
}

IWbemServices * GetWbemServices(const wstring namespace_) {
	IWbemLocator *pIWbemLocator = NULL;
	CoInitialize(NULL);
	HRESULT hRes = CoCreateInstance(
		CLSID_WbemAdministrativeLocator,
		NULL,
		CLSCTX_INPROC_SERVER | CLSCTX_LOCAL_SERVER,
		IID_IUnknown,
		(void **)&pIWbemLocator
	);
	IWbemServices *pWbemServices = NULL;

	VARIANT v1;
	VariantInit(&v1);
	V_VT(&v1) = VT_BSTR;
	V_BSTR(&v1) = SysAllocString(namespace_.c_str());

	if (SUCCEEDED(hRes))
	{
		hRes = pIWbemLocator->ConnectServer(
			(BSTR)(namespace_.c_str()),  // Namespace
			NULL,          // Userid
			NULL,           // PW
			NULL,           // Locale
			0,              // flags
			NULL,           // Authority
			NULL,           // Context
			&pWbemServices
		);

		pIWbemLocator->Release(); // Free memory resources.
		// Use pWbemServices
	}
	return pWbemServices;
}

int CreateClass(wchar_t* namespace_, wchar_t* className)
{
	//MessageBox(0, 0, 0, MB_OK);

	IWbemServices* pWbemServices = GetWbemServices(namespace_);
	IWbemContext* pCtx = 0;
	IWbemClassObject* pNewClass = 0;
	IWbemCallResult* pResult = 0;
	HRESULT hRes = pWbemServices->GetObject(0, 0, pCtx, &pNewClass, &pResult);

	VARIANT v;
	VariantInit(&v);
	V_VT(&v) = VT_BSTR;
	//const wchar_t* szClassName = className.c_str();
	V_BSTR(&v) = SysAllocString(className);
	BSTR Class = SysAllocString(L"__CLASS");

	hRes = pNewClass->Put(Class, 0, &v, 0);
	SysFreeString(Class);
	VariantClear(&v);

	hRes = pWbemServices->PutClass(pNewClass, 0, pCtx, &pResult);
	pNewClass->Release();
	
	// Clean up
	pWbemServices->Release();

	return 0;
}

int CreateProperty(wchar_t* namespace_, wchar_t* className, wchar_t* propertyName, wchar_t* value)
{
	IWbemServices* pWbemServices = GetWbemServices(namespace_);
	IWbemContext* pCtx = 0;
	IWbemClassObject* pNewClass = 0;
	IWbemCallResult* pResult = 0;
	HRESULT hRes = pWbemServices->GetObject((BSTR)(className), 0, pCtx, &pNewClass, &pResult);

	//const wchar_t* szPropertyName = className.c_str();
	BSTR newProp = SysAllocString(propertyName);

	VARIANT v;
	VariantInit(&v);
	V_VT(&v) = VT_BSTR;
	V_BSTR(&v) = SysAllocString(value);

	hRes = pNewClass->Put(newProp, 0, &v, CIM_STRING);
	hRes = pWbemServices->PutClass(pNewClass, 0, pCtx, &pResult);
	pNewClass->Release();
	// Clean up
	pWbemServices->Release();

	return 0;
}


int DeleteProperty(wchar_t* namespace_, wchar_t* className, wchar_t* propertyName)
{
	IWbemServices* pWbemServices = GetWbemServices(namespace_);
	IWbemContext* pCtx = 0;
	IWbemClassObject* pNewClass = 0;
	IWbemCallResult* pResult = 0;
	HRESULT hRes = pWbemServices->GetObject((BSTR)(className), 0, pCtx, &pNewClass, &pResult);

	BSTR propToDelete = SysAllocString(propertyName);

	hRes = pNewClass->Delete(propToDelete);
	hRes = pWbemServices->PutClass(pNewClass, 0, pCtx, &pResult);
	pNewClass->Release();
	// Clean up
	pWbemServices->Release();

	return 0;
}