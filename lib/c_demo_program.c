/* TEMPLATE GENERATED TESTCASE FILE
Filename: CWE369_Divide_by_Zero__float_connect_socket_01.c
Label Definition File: CWE369_Divide_by_Zero__float.label.xml
Template File: sources-sinks-01.tmpl.c
*/
/*
 * @description
 * CWE: 369 Divide by Zero
 * BadSource: connect_socket Read data using a connect socket (client side)
 * GoodSource: A hardcoded non-zero number (two)
 * Sinks:
 *    GoodSink: Check value of or near zero before dividing
 *    BadSink : Divide a constant by data
 * Flow Variant: 01 Baseline
 *
 * */

#include "std_testcase.h"



void CWE369_Divide_by_Zero__float_connect_socket_01_bad(float dataArray[])
{
    float data = 1;
#ifdef _WIN32
    WSADATA wsaData;
    int wsaDataInit = 0;
#endif
    fscanf(stdin, "%d", &data);
    data = 2;
    /* Initialize data */
}
