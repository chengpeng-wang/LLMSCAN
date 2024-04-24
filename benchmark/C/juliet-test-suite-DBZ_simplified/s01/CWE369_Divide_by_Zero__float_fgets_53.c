/* TEMPLATE GENERATED TESTCASE FILE
Filename: CWE369_Divide_by_Zero__float_fgets_53a.c
Label Definition File: CWE369_Divide_by_Zero__float.label.xml
Template File: sources-sinks-53a.tmpl.c
*/
/*
 * @description
 * CWE: 369 Divide by Zero
 * BadSource: fgets Read data from the console using fgets()
 * GoodSource: A hardcoded non-zero number (two)
 * Sinks:
 *    GoodSink: Check value of or near zero before dividing
 *    BadSink : Divide a constant by data
 * Flow Variant: 53 Data flow: data passed as an argument from one function through two others to a fourth; all four functions are in different source files
 *
 * */

#include "std_testcase.h"

#include <math.h>

#define CHAR_ARRAY_SIZE 20

#ifndef OMITBAD

/* bad function declaration */
void CWE369_Divide_by_Zero__float_fgets_53b_badSink(float data);

void CWE369_Divide_by_Zero__float_fgets_53_bad()
{
    float data;
    /* Initialize data */
    data = 0.0F;
    {
        char inputBuffer[CHAR_ARRAY_SIZE];
        /* POTENTIAL FLAW: Use a value input from the console using fgets() */
        if (fgets(inputBuffer, CHAR_ARRAY_SIZE, stdin) != NULL)
        {
            /* Convert to float */
            data = (float)atof(inputBuffer);
        }
        else
        {
            printLine("fgets() failed.");
        }
    }
    CWE369_Divide_by_Zero__float_fgets_53b_badSink(data);
}

#endif /* OMITBAD */

#ifndef OMITGOOD

/* goodG2B uses the GoodSource with the BadSink */
void CWE369_Divide_by_Zero__float_fgets_53b_goodG2BSink(float data);

static void goodG2B()
{
    float data;
    /* Initialize data */
    data = 0.0F;
    /* FIX: Use a hardcoded number that won't a divide by zero */
    data = 2.0F;
    CWE369_Divide_by_Zero__float_fgets_53b_goodG2BSink(data);
}

/* goodB2G uses the BadSource with the GoodSink */
void CWE369_Divide_by_Zero__float_fgets_53b_goodB2GSink(float data);

static void goodB2G()
{
    float data;
    /* Initialize data */
    data = 0.0F;
    {
        char inputBuffer[CHAR_ARRAY_SIZE];
        /* POTENTIAL FLAW: Use a value input from the console using fgets() */
        if (fgets(inputBuffer, CHAR_ARRAY_SIZE, stdin) != NULL)
        {
            /* Convert to float */
            data = (float)atof(inputBuffer);
        }
        else
        {
            printLine("fgets() failed.");
        }
    }
    CWE369_Divide_by_Zero__float_fgets_53b_goodB2GSink(data);
}

void CWE369_Divide_by_Zero__float_fgets_53_good()
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
    CWE369_Divide_by_Zero__float_fgets_53_good();
    printLine("Finished good()");
#endif /* OMITGOOD */
#ifndef OMITBAD
    printLine("Calling bad()...");
    CWE369_Divide_by_Zero__float_fgets_53_bad();
    printLine("Finished bad()");
#endif /* OMITBAD */
    return 0;
}

#endif
/* TEMPLATE GENERATED TESTCASE FILE
Filename: CWE369_Divide_by_Zero__float_fgets_53b.c
Label Definition File: CWE369_Divide_by_Zero__float.label.xml
Template File: sources-sinks-53b.tmpl.c
*/
/*
 * @description
 * CWE: 369 Divide by Zero
 * BadSource: fgets Read data from the console using fgets()
 * GoodSource: A hardcoded non-zero number (two)
 * Sinks:
 *    GoodSink: Check value of or near zero before dividing
 *    BadSink : Divide a constant by data
 * Flow Variant: 53 Data flow: data passed as an argument from one function through two others to a fourth; all four functions are in different source files
 *
 * */



#define CHAR_ARRAY_SIZE 20

#ifndef OMITBAD

/* bad function declaration */
void CWE369_Divide_by_Zero__float_fgets_53c_badSink(float data);

void CWE369_Divide_by_Zero__float_fgets_53b_badSink(float data)
{
    CWE369_Divide_by_Zero__float_fgets_53c_badSink(data);
}

#endif /* OMITBAD */

#ifndef OMITGOOD

/* goodG2B uses the GoodSource with the BadSink */
void CWE369_Divide_by_Zero__float_fgets_53c_goodG2BSink(float data);

void CWE369_Divide_by_Zero__float_fgets_53b_goodG2BSink(float data)
{
    CWE369_Divide_by_Zero__float_fgets_53c_goodG2BSink(data);
}

/* goodB2G uses the BadSource with the GoodSink */
void CWE369_Divide_by_Zero__float_fgets_53c_goodB2GSink(float data);

void CWE369_Divide_by_Zero__float_fgets_53b_goodB2GSink(float data)
{
    CWE369_Divide_by_Zero__float_fgets_53c_goodB2GSink(data);
}

#endif /* OMITGOOD */
/* TEMPLATE GENERATED TESTCASE FILE
Filename: CWE369_Divide_by_Zero__float_fgets_53c.c
Label Definition File: CWE369_Divide_by_Zero__float.label.xml
Template File: sources-sinks-53c.tmpl.c
*/
/*
 * @description
 * CWE: 369 Divide by Zero
 * BadSource: fgets Read data from the console using fgets()
 * GoodSource: A hardcoded non-zero number (two)
 * Sinks:
 *    GoodSink: Check value of or near zero before dividing
 *    BadSink : Divide a constant by data
 * Flow Variant: 53 Data flow: data passed as an argument from one function through two others to a fourth; all four functions are in different source files
 *
 * */



#define CHAR_ARRAY_SIZE 20

#ifndef OMITBAD

/* bad function declaration */
void CWE369_Divide_by_Zero__float_fgets_53d_badSink(float data);

void CWE369_Divide_by_Zero__float_fgets_53c_badSink(float data)
{
    CWE369_Divide_by_Zero__float_fgets_53d_badSink(data);
}

#endif /* OMITBAD */

#ifndef OMITGOOD

/* goodG2B uses the GoodSource with the BadSink */
void CWE369_Divide_by_Zero__float_fgets_53d_goodG2BSink(float data);

void CWE369_Divide_by_Zero__float_fgets_53c_goodG2BSink(float data)
{
    CWE369_Divide_by_Zero__float_fgets_53d_goodG2BSink(data);
}

/* goodB2G uses the BadSource with the GoodSink */
void CWE369_Divide_by_Zero__float_fgets_53d_goodB2GSink(float data);

void CWE369_Divide_by_Zero__float_fgets_53c_goodB2GSink(float data)
{
    CWE369_Divide_by_Zero__float_fgets_53d_goodB2GSink(data);
}

#endif /* OMITGOOD */
/* TEMPLATE GENERATED TESTCASE FILE
Filename: CWE369_Divide_by_Zero__float_fgets_53d.c
Label Definition File: CWE369_Divide_by_Zero__float.label.xml
Template File: sources-sinks-53d.tmpl.c
*/
/*
 * @description
 * CWE: 369 Divide by Zero
 * BadSource: fgets Read data from the console using fgets()
 * GoodSource: A hardcoded non-zero number (two)
 * Sinks:
 *    GoodSink: Check value of or near zero before dividing
 *    BadSink : Divide a constant by data
 * Flow Variant: 53 Data flow: data passed as an argument from one function through two others to a fourth; all four functions are in different source files
 *
 * */



#define CHAR_ARRAY_SIZE 20

#ifndef OMITBAD

void CWE369_Divide_by_Zero__float_fgets_53d_badSink(float data)
{
    {
        /* POTENTIAL FLAW: Possibly divide by zero */
        int result = (int)(100.0 / data);
        printIntLine(result);
    }
}

#endif /* OMITBAD */

#ifndef OMITGOOD

/* goodG2B uses the GoodSource with the BadSink */
void CWE369_Divide_by_Zero__float_fgets_53d_goodG2BSink(float data)
{
    {
        /* POTENTIAL FLAW: Possibly divide by zero */
        int result = (int)(100.0 / data);
        printIntLine(result);
    }
}

/* goodB2G uses the BadSource with the GoodSink */
void CWE369_Divide_by_Zero__float_fgets_53d_goodB2GSink(float data)
{
    /* FIX: Check for value of or near zero before dividing */
    if(fabs(data) > 0.000001)
    {
        int result = (int)(100.0 / data);
        printIntLine(result);
    }
    else
    {
        printLine("This would result in a divide by zero");
    }
}

#endif /* OMITGOOD */
