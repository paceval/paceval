//Developed and tested with Node.js version 18.7.0

'use strict';

const compression = require('compression');
const express = require('express');
const app = express();
app.use(compression());
const ffi = require('ffi-napi');
const ref = require('ref-napi');

const child_process = require("child_process");

const ArrayType = require('ref-array-napi');

const gc=require('js-gc');

var numberOfActiveComputations = 0;
var numberOfRequestslastGC = 0;
var numberOfGCs = 0;
var saveHeap = false;



const bodyParser = require('body-parser'); 
app.use(bodyParser.json({limit: '5mb'}));
app.use(bodyParser.urlencoded({limit: '5mb', extended: true}));

var versionNumber = 0;

var debugEnabled = true;//false;
let computationObject;
let ready = false;
let computationInfo = {}


function pacevalLibraryName()
{
    let pacevalLibrary_str = null;
    let platform = process.platform;
    let architecture = process.arch;

    if (((platform === 'win32') || (platform === 'win64')) && (architecture === 'x64'))
    {
        pacevalLibrary_str = 'paceval_win64i';
    }
    else if ((platform === 'linux') && (architecture === 'x64'))
    {
        pacevalLibrary_str = './libpaceval_linux_sharedLIB.so';
    }
    else if ((platform === 'linux') && (architecture === 'arm64'))
    {
        pacevalLibrary_str = './libpacevalARM64_sharedLIB.so';
    }
    else if ((platform === 'darwin') && (architecture === 'arm64'))
    {
        pacevalLibrary_str = './libpaceval_macOS_dynamicLIB.dylib';
    }
    else
    {
        throw new Error('unsupported platform and architecture for pacevalLibrary : '
                        + platform + ' ' + architecture + '-please, contact us via info@paceval.com')
    }
    
    return pacevalLibrary_str;
}


var intPtr_ffi = ref.refType('int');
var doubleArray_ffi = ArrayType('double');
var pointerArray_ffi = ArrayType('pointer');
var doublePtr_ffi = ref.refType('double');
var double_ffi = ref.types.double;
var longPtr_ffi = ref.refType('long');

let functionId

var pacevalLibrary_ffi = ffi.Library(pacevalLibraryName(),
{
    'pacevalLibrary_Initialize': [ 'bool', [ 'string' ] ],
    'pacevalLibrary_CreateComputation': [ 'pointer', [ 'string', 'uint32', 'string', 'int', 'pointer' ] ],
    'pacevalLibrary_GetIsError': [ 'bool', [ 'pointer' ] ],
    'pacevalLibrary_dmathv': [ 'double', [ 'pointer', intPtr_ffi , 'string', 'uint32', 'string', doubleArray_ffi ] ],   
    'pacevalLibrary_GetErrorInformation': [ 'int', [ 'pointer', 'char*', longPtr_ffi ] ],   
    'pacevalLibrary_CreateErrorInformationText': [ 'int', [ 'pointer', 'char*', 'char*' ] ],
    'pacevalLibrary_dGetComputationResult': [ 'double', [ 'pointer', doubleArray_ffi , doublePtr_ffi , doublePtr_ffi ] ],
    'pacevalLibrary_dGetComputationResultExt': [ 'bool', [ 'pointer', doubleArray_ffi , 'uint32', doublePtr_ffi , doublePtr_ffi , doublePtr_ffi, intPtr_ffi ] ],
    'pacevalLibrary_dGetMultipleComputationsResults': [ 'bool', [ pointerArray_ffi, 'uint32', doubleArray_ffi , doublePtr_ffi , doublePtr_ffi , doublePtr_ffi, intPtr_ffi ] ],
    'pacevalLibrary_dConvertFloatToString': [ 'int', [ 'pointer', double_ffi ] ],
    'pacevalLibrary_GetComputationInformationXML': [ 'uint32', [ 'pointer', 'char*' ] ],
    'pacevalLibrary_GetComputationVersionString': [ 'int', [ 'pointer', 'char*' ] ],
    'pacevalLibrary_DeleteComputation': [ 'bool', [ 'pointer' ] ],
}); 

function sleepTime(ms) 
{
  return new Promise(resolve => setTimeout(resolve, ms));
}

async function runGarbageCollection()
{
    if (debugEnabled == true)
        console.log(`start garbage collection - timestamp: ${new Date().toISOString()}`);
    
    await sleepTime(1000)
    child_process.execSync("sleep 1");
    await global.gc();
    
    if (debugEnabled == true)
    {
        console.log(`finished garbage collection - timestamp: ${new Date().toISOString()}`);
        console.log(``);
    }
}

function logMemoryUsed()
{
    let kbHeap = process.memoryUsage().heapUsed / 1024;
    let kbRoundedHeap = Math.round(kbHeap * 100) / 100;
    let kbExternal = process.memoryUsage().external / 1024;
    let kbRoundedExternal = Math.round(kbExternal * 100) / 100;
    
//  var errorType = ref.alloc('int');
    if (debugEnabled == true)
    {
        console.log(``);
        console.log(`- Status paceval. server ---------------------`);
        console.log(`Resident Set Size: ${ process.memoryUsage().rss / 1024 }K`);
        console.log(`Total Heap Size: ${ process.memoryUsage().heapTotal / 1024 }K`);
        console.log(`Heap allocated: ${kbRoundedHeap}K`);
        console.log(`External: ${kbRoundedExternal}K`);
    
//      console.log(`Array Computations: ${sizeof.sizeof(pacevalComputations_arr, true)}`);   
        console.log(`Active Computations: ${numberOfActiveComputations}`);
        console.log(`Number Of Requests since last GC: ${numberOfRequestslastGC}`);
        console.log(`Number Of GCs: ${numberOfGCs}`);
        console.log(`----------------------------------------------`);
    }

    if (numberOfRequestslastGC >= 250) //after 250 computations we will run a garbage collection
    {       
        numberOfRequestslastGC = 0;
        numberOfGCs++;
        
        if (global.gc) 
        {
            runGarbageCollection();
        } 
        else 
        {
            if (debugEnabled == true)
                console.warn('No GC hook for memory cleanup! Start your program as `node --expose-gc ./paceval-server.js --max-old-space-size=6000`.');
        }
    }
}





//---------------------------------------------------------------------------
//  handleCreateComputation
//  Creates a remote computation object with the specified attributes and returns its HANDLE: 
//  example http://paceval-service.com/CreateComputation/?functionString=-sin(x*cos(x))^(1/y)&numberOfVariables=2&variables=x;y&interval=yes
//
//  see  https://app.swaggerhub.com/apis-docs/paceval/paceval-service/4.04
//---------------------------------------------------------------------------
function initCreateComputation()
{

    if( !process.env.FUNCTION_STR || !process.env.NUM_VARS || !process.env.VARS || !process.env.INTERVAL || !process.env.FUNCTION_ID){
        console.log("Missing environment variables");
        process.exit(1);
    }

    functionId = process.env.FUNCTION_ID;

    let handle_pacevalComputation;
    let isError;
    const numberOfVariables = Number(process.env.NUM_VARS);
    let function10chars = '';
    let functionLength = 0;
    let interval = (process.env.INTERVAL === "true");
    const function_str = process.env.FUNCTION_STR;
    const variables_str = process.env.VARS.replace(/;/g, ' ');


    let now = require('performance-now');
    let success = false;

    if (debugEnabled == true)
        console.log(`handle create computation - timestamp: ${new Date().toISOString()}`);

    if (numberOfActiveComputations == 0)
    {
        success = pacevalLibrary_ffi.pacevalLibrary_Initialize(null);
        
        if (debugEnabled == true)
            console.log(`paceval. initialize library: ${success}`);
    }

    let timeCreate = now(); 
    handle_pacevalComputation = pacevalLibrary_ffi.pacevalLibrary_CreateComputation(function_str,
                                        numberOfVariables, variables_str, interval, null);
    timeCreate = (now() - timeCreate) / 1000;
    
    numberOfActiveComputations++;
    isError = pacevalLibrary_ffi.pacevalLibrary_GetIsError(handle_pacevalComputation);
       
    if (debugEnabled == true)      
        console.log(`created new computation handle_pacevalComputation: ${handle_pacevalComputation.address()}`);


    functionLength = function_str.length;
    function10chars = function_str.substring(0, 10);
    if (functionLength > 10)
    {
        function10chars = function10chars + '(...)';
    }

    let maxLengthStr = pacevalLibrary_ffi.pacevalLibrary_CreateErrorInformationText(handle_pacevalComputation, null, null);
    let errorMessage_str = Buffer.alloc(maxLengthStr, 0, 'ascii');
    let errorDetails_str = Buffer.alloc(maxLengthStr, 0, 'ascii');
    maxLengthStr = pacevalLibrary_ffi.pacevalLibrary_CreateErrorInformationText(handle_pacevalComputation,
                   errorMessage_str, errorDetails_str);

    let errorType = ref.alloc('int');
    if (versionNumber == 0)
        versionNumber = pacevalLibrary_ffi.pacevalLibrary_dmathv(null, errorType, 'paceval_VersionNumber', 0, '', null);
    
    let errorPosition = ref.alloc('long');
    let errorPositionLong = -1;
    
    errorType = pacevalLibrary_ffi.pacevalLibrary_GetErrorInformation(handle_pacevalComputation, null, errorPosition);
    
    if (errorPosition.deref() == -1)
        errorPositionLong = '';
    else
        errorPositionLong = errorPosition.deref();



    if (debugEnabled == true)
    {
        console.log('function10chars:' + function10chars);
        console.log('errorType:' + errorType);
        console.log('error-position:' + errorPositionLong);
        console.log('error-type' + errorDetails_str.toString().replace(/\0/g, ''));
        console.log('error-message' + errorMessage_str.toString().replace(/\0/g, ''));
        console.log('time-create:' + timeCreate.toFixed(6) + 's');
        console.log('version-number:' + versionNumber );

        console.log('maxLengthStr:' + maxLengthStr);
        console.log('isError:' + isError);
        console.log(`number of active computations: ${numberOfActiveComputations}`);

    }
    
    logMemoryUsed();
    if (debugEnabled == true)
        console.log(``);

    ready = !Boolean(isError);
    computationInfo = {
        'handle_pacevalComputation': functionId,
        'function-10chars': function10chars,
        'function-length': functionLength,
        'error-type-number': errorType,
        'error-position': errorPositionLong,
        'error-type': errorDetails_str.toString().replace(/\0/g, ''),
        'error-message': errorMessage_str.toString().replace(/\0/g, ''),
        'time-create': timeCreate.toFixed(6) + 's',
        'version-number': versionNumber

    }
    return handle_pacevalComputation;
}

//---------------------------------------------------------------------------
//  handleGetComputationResult
//  Solves the computation with the variables declared by /CreateComputation and with the given values: 
//  example http://paceval-service.com/GetComputationResult/?handle_pacevalComputation=140523460713760&values=0.5;2
//
//  see  https://app.swaggerhub.com/apis-docs/paceval/paceval-service/4.04
//---------------------------------------------------------------------------
function handleGetComputationResult(req, res)
{

    let isError = false;
    let numberOfVariables = Number(process.env.NUM_VARS);;
    let interval = (process.env.INTERVAL === "true");
    let values_ar = [];



    if (debugEnabled == true)
        console.log(`reuse computation handle_pacevalComputation: ${computationObject.address()}`);

    let handle_pacevalComputation = computationObject; //[1] 'pointer' returned from pacevalLibrary_ffi.pacevalLibrary_CreateComputation()


    if (req.query.values != null) //GET    
        values_ar = JSON.parse('[' + req.query.values.replace(/;/g, ',') + ']');
    else //POST
        values_ar = JSON.parse('[' + req.body.values.replace(/;/g, ',') + ']');

    let now = require('performance-now');

    if (debugEnabled == true)
        console.log(`handle get result for computation handle_pacevalComputation: ${computationObject.address()} - timestamp: ${new Date().toISOString()}`);

    let valuesVariablesArray = new doubleArray_ffi(numberOfVariables);
    let iCount = 0;

    for (iCount = 0; iCount < numberOfVariables; iCount++)
    {
        valuesVariablesArray[iCount] = values_ar[iCount];
    }

    let trustedMinResult = ref.alloc('double');
    let trustedMaxResult = ref.alloc('double');
    let result_str = Buffer.alloc(25, 0, 'ascii');
    let trustedMinResult_str = Buffer.alloc(25, 0, 'ascii');
    let trustedMaxResult_str = Buffer.alloc(25, 0, 'ascii');

    let result = 0;

    let timeCalculate = now();
    if (interval == false)
    {
        result = pacevalLibrary_ffi.pacevalLibrary_dGetComputationResult(handle_pacevalComputation,
            valuesVariablesArray, null, null);
    }
    else
    {
        result = pacevalLibrary_ffi.pacevalLibrary_dGetComputationResult(handle_pacevalComputation,
            valuesVariablesArray, trustedMinResult, trustedMaxResult);
    }
    timeCalculate = (now() - timeCalculate) / 1000;
      
    isError = pacevalLibrary_ffi.pacevalLibrary_GetIsError(handle_pacevalComputation);
    let success = pacevalLibrary_ffi.pacevalLibrary_dConvertFloatToString(result_str, result);

    if (interval == true)
    {
        success = pacevalLibrary_ffi.pacevalLibrary_dConvertFloatToString(trustedMinResult_str, trustedMinResult.deref());
        success = pacevalLibrary_ffi.pacevalLibrary_dConvertFloatToString(trustedMaxResult_str, trustedMaxResult.deref());
    }

    let maxLengthStr = pacevalLibrary_ffi.pacevalLibrary_CreateErrorInformationText(handle_pacevalComputation, null, null);
    let errorMessage_str = Buffer.alloc(maxLengthStr, 0, 'ascii');
    let errorDetails_str = Buffer.alloc(maxLengthStr, 0, 'ascii');
    maxLengthStr = pacevalLibrary_ffi.pacevalLibrary_CreateErrorInformationText(handle_pacevalComputation,
                   errorMessage_str, errorDetails_str);

    let errorType = ref.alloc('int');
    if (versionNumber == 0)
        versionNumber = pacevalLibrary_ffi.pacevalLibrary_dmathv(null, errorType, 'paceval_VersionNumber', 0, '', null);
    
    let errorPosition = ref.alloc('long');
    let errorPositionLong = -1;
    
    errorType = pacevalLibrary_ffi.pacevalLibrary_GetErrorInformation(handle_pacevalComputation, null, errorPosition);
    
    if (errorPosition.deref() == -1)
        errorPositionLong = '';
    else
        errorPositionLong = errorPosition.deref();
    
    if (errorType != 0)
    {
        result_str = "";
        if (interval == true)
        {
            trustedMinResult_str = "";
            trustedMaxResult_str = "";
        }
    }

    let return_arr =
    {
        'handle_pacevalComputation': functionId,
        'result': result_str.toString().replace(/\0/g, ''),
        'interval-min-result': trustedMinResult_str.toString().replace(/\0/g, ''),
        'interval-max-result': trustedMaxResult_str.toString().replace(/\0/g, ''),
        'error-type-number': errorType,
        'error-position': errorPositionLong,
        'error-type': errorDetails_str.toString().replace(/\0/g, ''),
        'error-message': errorMessage_str.toString().replace(/\0/g, ''),
        'time-calculate': timeCalculate.toFixed(6) + 's',
        'version-number': versionNumber
    };

    res.setHeader('Content-Type', 'application/json');
    res.end(JSON.stringify(return_arr));

    if (debugEnabled == true)
        console.log(`time to calculate: ${timeCalculate.toFixed(6) + 's'}`);

    
    logMemoryUsed();
    if (debugEnabled == true)
        console.log(``);
}

//---------------------------------------------------------------------------
//  handleGetComputationResultExt
//  Solves the computation with multiple values for the variables declared by /CreateComputation: 
//  example http://paceval-service.com/GetComputationResultExt/?handle_pacevalComputation=140523460713760&numberOfCalculations=2&values=0.5;2;0.5;4
//
//  see  https://app.swaggerhub.com/apis-docs/paceval/paceval-service/4.04
//---------------------------------------------------------------------------
function handleGetComputationResultExt(req, res)
{
    let numberOfCalculations = 0;
    let hasError = false;
    let numberOfVariables = Number(process.env.NUM_VARS);;
    let interval = (process.env.INTERVAL === "true");
    let values_str = '';
    let values_ar = [];

    if (req.query.numberOfCalculations != null) //GET
    {
        numberOfCalculations = parseInt(req.query.numberOfCalculations);
    }
    else //POST
    {
        numberOfCalculations = parseInt(req.body.numberOfCalculations);
    }



    if (debugEnabled == true)
        console.log(`handle get results for multiple values for variables handle_pacevalComputations: ${computationObject.address()} - timestamp: ${new Date().toISOString()}`);


    if (debugEnabled == true)
        console.log(`reuse computation handle_pacevalComputation: ${computationObject.address()}`);

    let handle_pacevalComputation = computationObject;



    if (req.query.values != null) //GET    
        values_str = req.query.values;
    else //POST  
        values_str = req.body.values;

    values_str = values_str.replace(/;/g, ',');
    values_ar = values_str.split(',');

    let now = require('performance-now');
    let iCount = 0;

    let valuesVariablesArray = new doubleArray_ffi(numberOfCalculations * numberOfVariables);
    for (iCount = 0; iCount < numberOfCalculations * numberOfVariables; iCount++)
    {
        valuesVariablesArray[iCount] = values_ar[iCount];
    }


    let resultsArray = Buffer.allocUnsafe(numberOfCalculations * 8 /*double 8 bytes*/); 
    let trustedMinResultsArray = Buffer.allocUnsafe(numberOfCalculations * 8 /*double 8 bytes*/);
    let trustedMaxResultsArray = Buffer.allocUnsafe(numberOfCalculations * 8 /*double 8 bytes*/);
    let errorTypesArray = Buffer.allocUnsafe(numberOfCalculations * 4 /*int 4 bytes*/);

    let timeCalculate = now();
    
    if (interval == false)
    {
        hasError = pacevalLibrary_ffi.pacevalLibrary_dGetComputationResultExt(handle_pacevalComputation, 
                     valuesVariablesArray, numberOfCalculations, resultsArray, null, null, errorTypesArray);
    }       
    else
    {
        hasError = pacevalLibrary_ffi.pacevalLibrary_dGetComputationResultExt(handle_pacevalComputation, 
                     valuesVariablesArray, numberOfCalculations, resultsArray, trustedMinResultsArray, trustedMaxResultsArray, errorTypesArray);
    }
    timeCalculate = (now() - timeCalculate) / 1000;

    let errorType = ref.alloc('int');
    if (versionNumber == 0)
        versionNumber = pacevalLibrary_ffi.pacevalLibrary_dmathv(null, errorType, 'paceval_VersionNumber', 0, '', null);

    let resultsArray_ar = new Array(numberOfCalculations);
    let trustedMinResultsArray_ar = new Array(numberOfCalculations);
    let trustedMaxResultsArray_ar = new Array(numberOfCalculations);
    let errorTypesArray_ar = new Array(numberOfCalculations);
    let result_str = Buffer.alloc(25, 0, 'ascii');
    let trustedMinResult_str = Buffer.alloc(25, 0, 'ascii');
    let trustedMaxResult_str = Buffer.alloc(25, 0, 'ascii');
    let errorTypesArray_str = Buffer.alloc(25, 0, 'ascii');
    let success = false;
    let stringToAdd;
    let errorTypeInt;

    for (iCount = 0; iCount < numberOfCalculations; iCount++)
    {       
        errorTypeInt = errorTypesArray.readInt32LE(iCount * 4 /*int 4 bytes*/);
        errorTypesArray_ar[iCount] = errorTypeInt;

        if (errorTypeInt == 0) //no error
        {
            success = pacevalLibrary_ffi.pacevalLibrary_dConvertFloatToString(result_str, resultsArray.readDoubleLE(iCount * 8 /*double 8 bytes*/)); 
            stringToAdd = result_str.toString().replace(/\0/g, ''); 
            resultsArray_ar[iCount] = stringToAdd;
            result_str.fill(0);

            if (interval == true)
            {
                success = pacevalLibrary_ffi.pacevalLibrary_dConvertFloatToString(trustedMinResult_str, trustedMinResultsArray.readDoubleLE(iCount * 8 /*double 8 bytes*/));   
                stringToAdd = trustedMinResult_str.toString().replace(/\0/g, ''); 
                trustedMinResultsArray_ar[iCount] = stringToAdd;
                trustedMinResult_str.fill(0);

                success = pacevalLibrary_ffi.pacevalLibrary_dConvertFloatToString(trustedMaxResult_str, trustedMaxResultsArray.readDoubleLE(iCount * 8 /*double 8 bytes*/));   
                stringToAdd = trustedMaxResult_str.toString().replace(/\0/g, ''); 
                trustedMaxResultsArray_ar[iCount] = stringToAdd;
                trustedMaxResult_str.fill(0);
            }
        }
        else
        {
            resultsArray_ar[iCount] = '';
            if (interval == true)
            {
                trustedMinResultsArray_ar[iCount] = '';
                trustedMaxResultsArray_ar[iCount] = '';
            }
        }
    }

    let return_arr = 
    {
        'handle_pacevalComputation': functionId,
        'number-of-multiple-values': numberOfCalculations,
        'hasError': hasError,
        'results': resultsArray_ar,
        'interval-min-results': trustedMinResultsArray_ar,
        'interval-max-results': trustedMaxResultsArray_ar,
        'error-type-numbers': errorTypesArray_ar,
        'time-calculate': timeCalculate.toFixed(6) + 's',
        'version-number': versionNumber
    };

    res.setHeader('Content-Type', 'application/json');
    res.end(JSON.stringify(return_arr));

    if (debugEnabled == true)
        console.log(`time to calculate: ${timeCalculate.toFixed(6) + 's'}`);



    logMemoryUsed();
    if (debugEnabled == true)
        console.log(``);
}

//---------------------------------------------------------------------------
//  handleGetComputationInformationXML
//  A helper function for getting data from a computation object, such as the number of cores in the system, the number of threads used or the cache hits in the computations with that particular computation object: 
//  example http://paceval-service.com/GetComputationInformationXML?handle_pacevalComputation=140523460713760
//
//  see  https://app.swaggerhub.com/apis-docs/paceval/paceval-service/4.04
//---------------------------------------------------------------------------
function handleGetComputationInformationXML(req, res)
{

    if (debugEnabled == true)
        console.log(`handle get information as XML from computation handle_pacevalComputation: ${computationObject.address()} - timestamp: ${new Date().toISOString()}`);



    if (debugEnabled == true)
        console.log(`reuse computation handle_pacevalComputation: ${computationObject.address()}`);

    let handle_pacevalComputation = computationObject;


    let maxLengthXML = pacevalLibrary_ffi.pacevalLibrary_GetComputationInformationXML(handle_pacevalComputation, null);
    let informationXML_str = Buffer.alloc(maxLengthXML, 0, 'ascii');
    maxLengthXML = pacevalLibrary_ffi.pacevalLibrary_GetComputationInformationXML(handle_pacevalComputation,
                   informationXML_str);
                   
    let pacevalVersion_str = Buffer.alloc(2000, 0, 'ascii');
    pacevalLibrary_ffi.pacevalLibrary_GetComputationVersionString(handle_pacevalComputation,
        pacevalVersion_str);

    let errorType = ref.alloc('int');
    if (versionNumber == 0)
        versionNumber = pacevalLibrary_ffi.pacevalLibrary_dmathv(null, errorType, 'paceval_VersionNumber', 0, '', null);

    let return_arr =
    {
        'information-XML': informationXML_str.toString().replace(/(?:\\[rn]|[\r\n])/g,'<br>').replace(/\0/g, ''),
        'version-details': pacevalVersion_str.toString().replace(/\0/g, ''),
        'version-number': versionNumber
    }; 

    res.setHeader('Content-Type', 'application/json');
    res.end(JSON.stringify(return_arr));

   
    if (debugEnabled == true)
    {
        console.log(`deletion timer prolonged by 1 hour for computation handle_pacevalComputation: ${computationObject.address()}`);
        console.log(`number of active computations: ${numberOfActiveComputations}`);
    }
    
    logMemoryUsed();
    if (debugEnabled == true)
        console.log(``);
}

//---------------------------------------------------------------------------
//  handleGetErrorInformation
//  Returns the computation object error type value: 
//  example http://paceval-service.com/GetErrorInformation/?handle_pacevalComputation=140523460713760
// 
//  see  https://app.swaggerhub.com/apis-docs/paceval/paceval-service/4.04
//---------------------------------------------------------------------------
function handleGetErrorInformation(req, res)
{
    let hasError = false;


    if (debugEnabled == true)
        console.log(`handle get error information from computation handle_pacevalComputation: ${computationObject.address()} - timestamp: ${new Date().toISOString()}`);


    if (debugEnabled == true)
        console.log(`reuse computation handle_pacevalComputation: ${computationObject.address()}`);

    let handle_pacevalComputation = computationObject;

    
    hasError = pacevalLibrary_ffi.pacevalLibrary_GetIsError(handle_pacevalComputation);
    
    let maxLengthStr = pacevalLibrary_ffi.pacevalLibrary_CreateErrorInformationText(handle_pacevalComputation, null, null);
    let errorMessage_str = Buffer.alloc(maxLengthStr, 0, 'ascii');
    let errorDetails_str = Buffer.alloc(maxLengthStr, 0, 'ascii');
    maxLengthStr = pacevalLibrary_ffi.pacevalLibrary_CreateErrorInformationText(handle_pacevalComputation,
                   errorMessage_str, errorDetails_str); 
        
    let errorOperator_str = Buffer.alloc(255, 0, 'ascii');
    let errorPosition = ref.alloc('int32');
    let errorPositionLong = -1;
    
    let errorTypeNumer = pacevalLibrary_ffi.pacevalLibrary_GetErrorInformation(handle_pacevalComputation, errorOperator_str, errorPosition); 
        
    if (errorPosition.deref() == -1)
        errorPositionLong = '';
    else
        errorPositionLong = errorPosition.deref();
    
    let errorType = ref.alloc('int');
    if (versionNumber == 0)
        versionNumber = pacevalLibrary_ffi.pacevalLibrary_dmathv(null, errorType, 'paceval_VersionNumber', 0, '', null);

    let return_arr =
    {
        'hasError': hasError,
        'error-type-number': errorTypeNumer,
        'error-position': errorPositionLong,
        'error-operator': errorOperator_str.toString().replace(/\0/g, ''),
        'error-type': errorDetails_str.toString().replace(/\0/g, ''),
        'error-message': errorMessage_str.toString().replace(/\0/g, ''),
        'version-number': versionNumber
    }; 
    
    res.setHeader('Content-Type', 'application/json');
    res.end(JSON.stringify(return_arr));

   
    if (debugEnabled == true)
    {
        console.log(`deletion timer prolonged by 1 hour for computation handle_pacevalComputation: ${computationObject.address()}`);
        console.log(`number of active computations: ${numberOfActiveComputations}`); 
    }
    
    logMemoryUsed();
    if (debugEnabled == true)
        console.log(``);
}

function handleGETandPOST(req, res, urlGET, urlPOST)
{

    numberOfRequestslastGC++;
    if ((req.query.call != null) || (urlGET != null)) //GET
    {
        if ((req.query.call == 'paceval_GetComputationResult') || (urlGET == 'GetComputationResult'))
        {

            handleGetComputationResult(req, res);
            return;
        }
        else if ((req.query.call == 'paceval_GetComputationResultExt') || (urlGET === 'GetComputationResultExt'))
        {

            handleGetComputationResultExt(req, res);
            return;
        }
        else if ((req.query.call == 'paceval_GetErrorInformation') || (urlGET === 'GetErrorInformation'))
        {

            handleGetErrorInformation(req, res);
            return;
        }
        else if ((req.query.call == 'paceval_GetComputationInformationXML') || (urlGET === 'GetComputationInformationXML'))
        {
            handleGetComputationInformationXML(req, res);
            return;
        }
        else 
        {
            res.status(500).json({ error: 'missing parameters' });
            return;
        }
    }
    else if ((req.body.call != null) || (urlPOST != null)) //POST
    {
       if ((req.body.call == 'paceval_GetComputationResult') || (urlPOST == 'GetComputationResult'))
        {
            handleGetComputationResult(req, res);
            return;
        }
        else if ((req.body.call == 'paceval_GetComputationResultExt') || (urlPOST == 'GetComputationResultExt'))  
        {
            handleGetComputationResultExt(req, res);
            return;
        }
        else if ((req.body.call == 'paceval_GetErrorInformation') || (urlPOST == 'GetErrorInformation'))  
        {

            handleGetErrorInformation(req, res);
            return;
        }
        else if ((req.body.call == 'paceval_GetComputationInformationXML') || (urlPOST == 'GetComputationInformationXML'))  
        {
        
            handleGetComputationInformationXML(req, res);
            return;
        }
        else 
        {
            res.status(500).json({ error: 'missing parameters' });
            return;
        }
    }

    res.status(500).json({ error: 'missing parameters' });
    return;
}; 

app.get('/', (req, res) =>
{
    handleGETandPOST(req, res, null, null);
});

app.post('/', (req, res) =>
{
    handleGETandPOST(req, res, null, null);
});

app.get("/GetComputation/", (req, res) =>
{
    res.setHeader('Content-Type', 'application/json');
    res.end(JSON.stringify(computationInfo));
});


app.get('/GetComputationResult/', (req, res) =>
{
    handleGETandPOST(req, res, 'GetComputationResult', null);
});

app.post('/GetComputationResult/', (req, res) =>
{
    handleGETandPOST(req, res, null, 'GetComputationResult');
});

app.get('/GetComputationResultExt/', (req, res) =>
{
    handleGETandPOST(req, res, 'GetComputationResultExt', null);
});

app.post('/GetComputationResultExt/', (req, res) =>
{
    handleGETandPOST(req, res, null, 'GetComputationResultExt');
});

app.get('/GetErrorInformation/', (req, res) =>
{
    handleGETandPOST(req, res, 'GetErrorInformation', null);
});

app.post('/GetErrorInformation/', (req, res) =>
{
    handleGETandPOST(req, res, null, 'GetErrorInformation');
});

app.get('/GetComputationInformationXML/', (req, res) =>
{
    handleGETandPOST(req, res, 'GetComputationInformationXML', null);
});

app.post('/GetComputationInformationXML/', (req, res) =>
{
    handleGETandPOST(req, res, null, 'GetComputationInformationXML');
});

app.get('/health',(req,res)=> {
    res.send ("Healthiness check passed");
});

app.get('/ready',(req,res)=> {
    if (ready){
        res.send ("Readiness check passed");
    }
    else{
        res.status(500).send("Service not ready");
    }
});

// Listen to the App Engine-specified port, or 8080 otherwise
const PORT = process.env.PORT || 8080;

app.listen(PORT, () =>
{
    console.log(`paceval-service listening on port ${PORT}...`);
    computationObject = initCreateComputation();
    logMemoryUsed();
    if (debugEnabled == true)
        console.log(``);
});
