/* TEMPLATE GENERATED TESTCASE FILE
Filename: CWE369_Divide_by_Zero__int_zero_divide_54a.c
Label Definition File: CWE369_Divide_by_Zero__int.label.xml
Template File: sources-sinks-54a.tmpl.c
*/
/*
 * @description
 * CWE: 369 Divide by Zero
 * BadSource: zero Fixed value of zero
 * GoodSource: Non-zero
 * Sinks: divide
 *    GoodSink: Check for zero before dividing
 *    BadSink : Divide a constant by data
 * Flow Variant: 54 Data flow: data passed as an argument from one function through three others to a fifth; all five functions are in different source files
 *
 * */

#include "std_testcase.h"

#ifndef OMITBAD

/* bad function declaration */
void CWE369_Divide_by_Zero__int_zero_divide_54b_badSink(int data);

void CWE369_Divide_by_Zero__int_zero_divide_54_bad()
{
    int data;
    /* Initialize data */
    data = -1;
    /* POTENTIAL FLAW: Set data to zero */
    data = 0;
    CWE369_Divide_by_Zero__int_zero_divide_54b_badSink(data);
}

#endif /* OMITBAD */

#ifndef OMITGOOD

/* goodG2B uses the GoodSource with the BadSink */
void CWE369_Divide_by_Zero__int_zero_divide_54b_goodG2BSink(int data);

static void goodG2B()
{
    int data;
    /* Initialize data */
    data = -1;
    /* FIX: Use a value not equal to zero */
    data = 7;
    CWE369_Divide_by_Zero__int_zero_divide_54b_goodG2BSink(data);
}

/* goodB2G uses the BadSource with the GoodSink */
void CWE369_Divide_by_Zero__int_zero_divide_54b_goodB2GSink(int data);

static void goodB2G()
{
    int data;
    /* Initialize data */
    data = -1;
    /* POTENTIAL FLAW: Set data to zero */
    data = 0;
    CWE369_Divide_by_Zero__int_zero_divide_54b_goodB2GSink(data);
}

void CWE369_Divide_by_Zero__int_zero_divide_54_good()
{
    goodG2B();
    goodB2G();
}

#endif /* OMITGOOD */

/* Below is the main(). It is only used when building this testcase on
   its own for testing or for building a binary to use in testing binary
   analysis tools. It is not used when compiling all the testcases as one
   application, which is how source code analysis tools are tested. */

#ifdef INCLUDEMAIN

int main(int argc, char * argv[])
{
    /* seed randomness */
    srand( (unsigned)time(NULL) );
#ifndef OMITGOOD
    printLine("Calling good()...");
    CWE369_Divide_by_Zero__int_zero_divide_54_good();
    printLine("Finished good()");
#endif /* OMITGOOD */
#ifndef OMITBAD
    printLine("Calling bad()...");
    CWE369_Divide_by_Zero__int_zero_divide_54_bad();
    printLine("Finished bad()");
#endif /* OMITBAD */
    return 0;
}

#endif
/* TEMPLATE GENERATED TESTCASE FILE
Filename: CWE369_Divide_by_Zero__int_zero_divide_54b.c
Label Definition File: CWE369_Divide_by_Zero__int.label.xml
Template File: sources-sinks-54b.tmpl.c
*/
/*
 * @description
 * CWE: 369 Divide by Zero
 * BadSource: zero Fixed value of zero
 * GoodSource: Non-zero
 * Sinks: divide
 *    GoodSink: Check for zero before dividing
 *    BadSink : Divide a constant by data
 * Flow Variant: 54 Data flow: data passed as an argument from one function through three others to a fifth; all five functions are in different source files
 *
 * */


#ifndef OMITBAD

/* bad function declaration */
void CWE369_Divide_by_Zero__int_zero_divide_54c_badSink(int data);

void CWE369_Divide_by_Zero__int_zero_divide_54b_badSink(int data)
{
    CWE369_Divide_by_Zero__int_zero_divide_54c_badSink(data);
}

#endif /* OMITBAD */

#ifndef OMITGOOD

/* goodG2B uses the GoodSource with the BadSink */
void CWE369_Divide_by_Zero__int_zero_divide_54c_goodG2BSink(int data);

void CWE369_Divide_by_Zero__int_zero_divide_54b_goodG2BSink(int data)
{
    CWE369_Divide_by_Zero__int_zero_divide_54c_goodG2BSink(data);
}

/* goodB2G uses the BadSource with the GoodSink */
void CWE369_Divide_by_Zero__int_zero_divide_54c_goodB2GSink(int data);

void CWE369_Divide_by_Zero__int_zero_divide_54b_goodB2GSink(int data)
{
    CWE369_Divide_by_Zero__int_zero_divide_54c_goodB2GSink(data);
}

#endif /* OMITGOOD */
/* TEMPLATE GENERATED TESTCASE FILE
Filename: CWE369_Divide_by_Zero__int_zero_divide_54e.c
Label Definition File: CWE369_Divide_by_Zero__int.label.xml
Template File: sources-sinks-54e.tmpl.c
*/
/*
 * @description
 * CWE: 369 Divide by Zero
 * BadSource: zero Fixed value of zero
 * GoodSource: Non-zero
 * Sinks: divide
 *    GoodSink: Check for zero before dividing
 *    BadSink : Divide a constant by data
 * Flow Variant: 54 Data flow: data passed as an argument from one function through three others to a fifth; all five functions are in different source files
 *
 * */


#ifndef OMITBAD

void CWE369_Divide_by_Zero__int_zero_divide_54e_badSink(int data)
{
    /* POTENTIAL FLAW: Possibly divide by zero */
    printIntLine(100 / data);
}

#endif /* OMITBAD */

#ifndef OMITGOOD

/* goodG2B uses the GoodSource with the BadSink */
void CWE369_Divide_by_Zero__int_zero_divide_54e_goodG2BSink(int data)
{
    /* POTENTIAL FLAW: Possibly divide by zero */
    printIntLine(100 / data);
}

/* goodB2G uses the BadSource with the GoodSink */
void CWE369_Divide_by_Zero__int_zero_divide_54e_goodB2GSink(int data)
{
    /* FIX: test for a zero denominator */
    if( data != 0 )
    {
        printIntLine(100 / data);
    }
    else
    {
        printLine("This would result in a divide by zero");
    }
}

#endif /* OMITGOOD */
/* TEMPLATE GENERATED TESTCASE FILE
Filename: CWE369_Divide_by_Zero__int_zero_divide_54d.c
Label Definition File: CWE369_Divide_by_Zero__int.label.xml
Template File: sources-sinks-54d.tmpl.c
*/
/*
 * @description
 * CWE: 369 Divide by Zero
 * BadSource: zero Fixed value of zero
 * GoodSource: Non-zero
 * Sinks: divide
 *    GoodSink: Check for zero before dividing
 *    BadSink : Divide a constant by data
 * Flow Variant: 54 Data flow: data passed as an argument from one function through three others to a fifth; all five functions are in different source files
 *
 * */


#ifndef OMITBAD

/* bad function declaration */
void CWE369_Divide_by_Zero__int_zero_divide_54e_badSink(int data);

void CWE369_Divide_by_Zero__int_zero_divide_54d_badSink(int data)
{
    CWE369_Divide_by_Zero__int_zero_divide_54e_badSink(data);
}

#endif /* OMITBAD */

#ifndef OMITGOOD

/* goodG2B uses the GoodSource with the BadSink */
void CWE369_Divide_by_Zero__int_zero_divide_54e_goodG2BSink(int data);

void CWE369_Divide_by_Zero__int_zero_divide_54d_goodG2BSink(int data)
{
    CWE369_Divide_by_Zero__int_zero_divide_54e_goodG2BSink(data);
}

/* goodB2G uses the BadSource with the GoodSink */
void CWE369_Divide_by_Zero__int_zero_divide_54e_goodB2GSink(int data);

void CWE369_Divide_by_Zero__int_zero_divide_54d_goodB2GSink(int data)
{
    CWE369_Divide_by_Zero__int_zero_divide_54e_goodB2GSink(data);
}

#endif /* OMITGOOD */
/* TEMPLATE GENERATED TESTCASE FILE
Filename: CWE369_Divide_by_Zero__int_zero_divide_54c.c
Label Definition File: CWE369_Divide_by_Zero__int.label.xml
Template File: sources-sinks-54c.tmpl.c
*/
/*
 * @description
 * CWE: 369 Divide by Zero
 * BadSource: zero Fixed value of zero
 * GoodSource: Non-zero
 * Sinks: divide
 *    GoodSink: Check for zero before dividing
 *    BadSink : Divide a constant by data
 * Flow Variant: 54 Data flow: data passed as an argument from one function through three others to a fifth; all five functions are in different source files
 *
 * */


#ifndef OMITBAD

/* bad function declaration */
void CWE369_Divide_by_Zero__int_zero_divide_54d_badSink(int data);

void CWE369_Divide_by_Zero__int_zero_divide_54c_badSink(int data)
{
    CWE369_Divide_by_Zero__int_zero_divide_54d_badSink(data);
}

#endif /* OMITBAD */

#ifndef OMITGOOD

/* goodG2B uses the GoodSource with the BadSink */
void CWE369_Divide_by_Zero__int_zero_divide_54d_goodG2BSink(int data);

void CWE369_Divide_by_Zero__int_zero_divide_54c_goodG2BSink(int data)
{
    CWE369_Divide_by_Zero__int_zero_divide_54d_goodG2BSink(data);
}

/* goodB2G uses the BadSource with the GoodSink */
void CWE369_Divide_by_Zero__int_zero_divide_54d_goodB2GSink(int data);

void CWE369_Divide_by_Zero__int_zero_divide_54c_goodB2GSink(int data)
{
    CWE369_Divide_by_Zero__int_zero_divide_54d_goodB2GSink(data);
}

#endif /* OMITGOOD */
