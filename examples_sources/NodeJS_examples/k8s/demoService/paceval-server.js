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

var pacevalComputations_arr = [];
//[0] the address of 'pointer' returned from pacevalLibrary_ffi.pacevalLibrary_CreateComputation()
//[1] 'pointer' returned from pacevalLibrary_ffi.pacevalLibrary_CreateComputation()
//[2] milliseconds timeout to delete (0 means no timeout)
//[3] number of variables
//[4] interval 0:false 1:true
//[5] valid/not deleted 0:false 1:true

const deleteTimeout = 2000;


const bodyParser = require('body-parser'); 
app.use(bodyParser.json({limit: '5mb'}));
app.use(bodyParser.urlencoded({limit: '5mb', extended: true}));

var versionNumber = 0;

var debugEnabled = true;//false;

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
    if (debugEnabled == true) {
        let kbHeap = process.memoryUsage().heapUsed / 1024;
        let kbRoundedHeap = Math.round(kbHeap * 100) / 100;
        let kbExternal = process.memoryUsage().external / 1024;
        let kbRoundedExternal = Math.round(kbExternal * 100) / 100;
        console.log(`start garbage collection - timestamp: ${new Date().toISOString()}`);
        console.log('memory before cleanup:')
        console.log(`Resident Set Size: ${process.memoryUsage().rss / 1024}K`);
        console.log(`Total Heap Size: ${process.memoryUsage().heapTotal / 1024}K`);
        console.log(`Heap allocated: ${kbRoundedHeap}K`);
        console.log(`External: ${kbRoundedExternal}K`);
    }
    
    await sleepTime(1000)
    //child_process.execSync("sleep 1");
    await global.gc();
    //global.gc()
    
    if (debugEnabled == true)
    {
        let kbHeap = process.memoryUsage().heapUsed / 1024;
        let kbRoundedHeap = Math.round(kbHeap * 100) / 100;
        let kbExternal = process.memoryUsage().external / 1024;
        let kbRoundedExternal = Math.round(kbExternal * 100) / 100;
        console.log(`finished garbage collection - timestamp: ${new Date().toISOString()}`);
        console.log(`memory after cleanup:`)
        console.log(`Resident Set Size: ${process.memoryUsage().rss / 1024}K`);
        console.log(`Total Heap Size: ${process.memoryUsage().heapTotal / 1024}K`);
        console.log(`Heap allocated: ${kbRoundedHeap}K`);
        console.log(`External: ${kbRoundedExternal}K`);
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

    if (numberOfRequestslastGC >= 1) //after 250 computations we will run a garbage collection
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


function findEmptyComputationPos()
{
    let numberOfComputations = pacevalComputations_arr.length;
    let iCount = 0;

    for (iCount = 0; iCount < numberOfComputations; iCount++)
    {
        //pacevalComputations_arr[iCount][5] valid/not deleted 0:false 1:true
        if (pacevalComputations_arr[iCount][5] == 0)
        {
            return iCount;
        }
    }

    return -1;
}

function findComputationPos(handle_pacevalComputation_str)
{
    let numberOfComputations = pacevalComputations_arr.length;
    let iCount = 0;

    for (iCount = 0; iCount < numberOfComputations; iCount++)
    {
        //pacevalComputations_arr[iCount][5] valid/not deleted 0:false 1:true
        //pacevalComputations_arr[iCount][1] 'pointer' returned from pacevalLibrary_ffi.pacevalLibrary_CreateComputation()
        if ((pacevalComputations_arr[iCount][5] == 1) && (pacevalComputations_arr[iCount][1].address() == handle_pacevalComputation_str))
        {
            return iCount;
        }
    }

    if (debugEnabled == true)
        console.log(`not found computation handle_pacevalComputation: ${handle_pacevalComputation_str}`);

    return -1;
}

function deleteComputationTimer()
{
    let numberOfComputations = pacevalComputations_arr.length;
    let iCount = 0;
    let success = false;

    for (iCount = 0; iCount < numberOfComputations; iCount++)
    {
        //pacevalComputations_arr[iCount][5] valid/not deleted 0:false 1:true
        //pacevalComputations_arr[iCount][2] milliseconds timeout to delete
        if ((pacevalComputations_arr[iCount][5] == 1) && (Date.now().valueOf() > pacevalComputations_arr[iCount][2]))
        {
            //pacevalComputations_arr[iCount][1] 'pointer' returned from pacevalLibrary_ffi.pacevalLibrary_CreateComputation()
            success = pacevalLibrary_ffi.pacevalLibrary_DeleteComputation(pacevalComputations_arr[iCount][1]);

            if (success == true)
            {
                if (debugEnabled == true)
                {
                    console.log(`handle delete computation - timestamp: ${new Date().toISOString()}`);
                    //pacevalComputations_arr[iCount][0] the address of 'pointer' returned from pacevalLibrary_ffi.pacevalLibrary_CreateComputation()
                    console.log(`deleted computation handle_pacevalComputation: ${pacevalComputations_arr[iCount][1].address()}`);
                }
                pacevalComputations_arr[iCount][1] = null;
                pacevalComputations_arr[iCount][5] = 0; //[5] valid/not deleted 0:false 1:true
                numberOfActiveComputations--;

                if (debugEnabled == true)
                {
                    console.log(`number of active computations: ${numberOfActiveComputations}`);
                    console.log(``);
                }
            }
        }
    }

    setTimeout(deleteComputationTimer, deleteTimeout);
}


//---------------------------------------------------------------------------
//  handleCreateComputation
//  Creates a remote computation object with the specified attributes and returns its HANDLE: 
//  example http://paceval-service.com/CreateComputation/?functionString=-sin(x*cos(x))^(1/y)&numberOfVariables=2&variables=x;y&interval=yes
//
//  see  https://app.swaggerhub.com/apis-docs/paceval/paceval-service/4.04
//---------------------------------------------------------------------------
function handleCreateComputation(req, res, senddata_in)
{
    let handle_pacevalComputation = null;
    let isError = false;
    let numberOfVariables = 0;
    let function10chars = '';
    let functionLength = 0;
    let interval = false;
    let function_str = '';
    let variables_str = '';

    if (req.query.functionString != null) //GET
    {
        function_str = req.query.functionString;
        numberOfVariables = parseInt(req.query.numberOfVariables);
        variables_str = req.query.variables.replace(/;/g, ' ');
        let interval_str = req.query.interval;

        if ((interval_str == 'yes') || (interval_str == 'true'))
            interval = true;
    }
    else //POST
    {
        function_str = req.body.functionString;
        numberOfVariables = parseInt(req.body.numberOfVariables);
        variables_str = req.body.variables.replace(/;/g, ' ');
        let interval_str = req.body.interval;

        if ((interval_str == 'yes') || (interval_str == 'true'))
            interval = true;
    }

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

    let handle_pacevalComputation_addr = handle_pacevalComputation.address();

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

    let return_arr =
        {
            'handle_pacevalComputation': handle_pacevalComputation_addr,
            'function-10chars': function10chars,
            'function-length': functionLength,
            'error-type-number': errorType,
            'error-position': errorPositionLong,
            'error-type': errorDetails_str.toString().replace(/\0/g, ''),
            'error-message': errorMessage_str.toString().replace(/\0/g, ''),
            'time-create': timeCreate.toFixed(6) + 's',
            'version-number': versionNumber
        };

    if (senddata_in == true)
    {
        res.setHeader('Content-Type', 'application/json');
        res.end(JSON.stringify(return_arr));
    }

    if (debugEnabled == true)
        console.log(`time to create: ${timeCreate.toFixed(6) + 's'}`);

    let position = -1;
    position = findEmptyComputationPos();

    if (position >= 0)
    {
        if (debugEnabled == true)
            console.log(`reused Array Computations position: ${position}`);
    }
    else
    {
        position = pacevalComputations_arr.push([  ]) -1;

        if (debugEnabled == true)
            console.log(`created new Array Computations position: ${position}`);
    }

    pacevalComputations_arr[position][0] = handle_pacevalComputation.address(); //[0] the address of 'pointer' returned from pacevalLibrary_ffi.pacevalLibrary_CreateComputation()
    pacevalComputations_arr[position][1] = handle_pacevalComputation; //[1] 'pointer' returned from pacevalLibrary_ffi.pacevalLibrary_CreateComputation()
    pacevalComputations_arr[position][2] = Date.now().valueOf() + deleteTimeout; //[2] milliseconds timeout to delete (0 means no timeout)
    if (req.query.numberOfVariables != null) //GET
        pacevalComputations_arr[position][3] = parseInt(req.query.numberOfVariables); //[3] number of variables (GET)
    else //POST
        pacevalComputations_arr[position][3] = parseInt(req.body.numberOfVariables); //[3] number of variables (POST)
    if (interval == false)
        pacevalComputations_arr[position][4] = 0; //[4] interval: false
    else
        pacevalComputations_arr[position][4] = 1; //[4] interval: true
    pacevalComputations_arr[position][5] = 1; //[5] valid/not deleted: true

    if (debugEnabled == true)
    {
        console.log(`1 hour deletion timer created for computation handle_pacevalComputation: ${handle_pacevalComputation.address()}`);
        console.log(`number of active computations: ${numberOfActiveComputations}`);
        console.log(`array size: ${pacevalComputations_arr.length}`);
    }

    logMemoryUsed();
    if (debugEnabled == true)
        console.log(``);

    return handle_pacevalComputation_addr;
}

//---------------------------------------------------------------------------
//  handleGetComputationResult
//  Solves the computation with the variables declared by /CreateComputation and with the given values: 
//  example http://paceval-service.com/GetComputationResult/?handle_pacevalComputation=140523460713760&values=0.5;2
//
//  see  https://app.swaggerhub.com/apis-docs/paceval/paceval-service/4.04
//---------------------------------------------------------------------------
function handleGetComputationResult(req, res, handle_pacevalComputation_str_in)
{
    let handle_pacevalComputation_str = handle_pacevalComputation_str_in;

    let existingComputation = false;
    let isError = false;
    let numberOfVariables = 0;
    let interval = false;
    let values_ar = [];

    if (req.query.handle_pacevalComputation != null) //GET
    {
        if (handle_pacevalComputation_str == null)
            handle_pacevalComputation_str = req.query.handle_pacevalComputation;
    }
    else //POST
    {
        if (handle_pacevalComputation_str == null)
            handle_pacevalComputation_str = req.body.handle_pacevalComputation;
    }

    if (handle_pacevalComputation_str == null)
    {
        handle_pacevalComputation_str = handle_pacevalComputation_str_in;
    }

    let handle_pacevalComputation = null;
    let position = -1;

    if (handle_pacevalComputation_str != null)
    {
        position = findComputationPos(handle_pacevalComputation_str);
        if (position >= 0)
        {
            if (debugEnabled == true)
                console.log(`reuse computation handle_pacevalComputation: ${handle_pacevalComputation_str}`);

            handle_pacevalComputation = pacevalComputations_arr[position][1]; //[1] 'pointer' returned from pacevalLibrary_ffi.pacevalLibrary_CreateComputation()
            pacevalComputations_arr[position][2] = 0; //[2] milliseconds timeout to delete (0 means no timeout)
            numberOfVariables = pacevalComputations_arr[position][3]; //[3] number of variables

            if (pacevalComputations_arr[position][4] == 0) //[4] interval 0:false 1:true
                interval = false;
            else
                interval = true;

            existingComputation = true;
        }
        else
        {
            res.status(500).json({ error: 'handle_pacevalComputation does not exist' });

            return;
        }
    }
    else
    {
        res.status(500).json({ error: 'handle_pacevalComputation does not exist' });
        return;
    }

    if (req.query.values != null) //GET
        values_ar = JSON.parse('[' + req.query.values.replace(/;/g, ',') + ']');
    else //POST
        values_ar = JSON.parse('[' + req.body.values.replace(/;/g, ',') + ']');

    let now = require('performance-now');

    if (debugEnabled == true)
        console.log(`handle get result for computation handle_pacevalComputation: ${handle_pacevalComputation_str} - timestamp: ${new Date().toISOString()}`);

    let valuesVariablesArray = new doubleArray_ffi(numberOfVariables);
    let iCount = 0;

    for (iCount = 0; iCount < numberOfVariables; iCount++)
    {
        valuesVariablesArray[iCount] = values_ar[iCount];
    }

    let trustedMinResult = ref.alloc('double');
    let trustedMaxResult = ref.alloc('double');
    let timeCreate = 0;
    let result_str = Buffer.alloc(25, 0, 'ascii');
    let trustedMinResult_str = Buffer.alloc(25, 0, 'ascii');
    let trustedMaxResult_str = Buffer.alloc(25, 0, 'ascii');

    let handle_pacevalComputation_addr = handle_pacevalComputation.address();
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
            'handle_pacevalComputation': "",
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

    pacevalComputations_arr[position][2] = Date.now().valueOf() + deleteTimeout; //[2] milliseconds timeout to delete (0 means no timeout)

    if (debugEnabled == true)
    {
        console.log(`deletion timer prolonged by 1 hour for computation handle_pacevalComputation: ${handle_pacevalComputation_str}`);
        console.log(`number of active computations: ${numberOfActiveComputations}`);
    }

    logMemoryUsed();
    if (debugEnabled == true)
        console.log(``);
}




function handleGETandPOST(req, res, urlGET, urlPOST)
{
    let handle_pacevalComputation_str = '';

    numberOfRequestslastGC++;
    if ((req.query.call != null) || (urlGET != null)) //GET
    {
        if ((req.query.call == 'paceval') || (urlGET == 'Demo'))
        {
            if ((req.query.functionString == null) || (req.query.numberOfVariables == null) || (req.query.variables == null) || (req.query.values == null) || (req.query.interval == null))
            {
                res.status(500).json({ error: 'missing parameters' });
                return;
            }

            if (req.query.handle_pacevalComputation == null)
                handle_pacevalComputation_str = handleCreateComputation(req, res, false);
            else
                handle_pacevalComputation_str = req.query.handle_pacevalComputation;

            handleGetComputationResult(req, res, handle_pacevalComputation_str);

            handle_pacevalComputation_str = null;
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
        if ((req.body.call == 'paceval') || (urlPOST == 'Demo'))
        {
            if ((req.body.functionString == null) || (req.body.numberOfVariables == null) || (req.body.variables == null) || (req.body.values == null) || (req.body.interval == null))
            {
                res.status(500).json({ error: 'missing parameters' });
                return;
            }

            if (req.body.handle_pacevalComputation == null)
                handle_pacevalComputation_str = handleCreateComputation(req, res, false);
            else
                handle_pacevalComputation_str = req.body.handle_pacevalComputation;

            handleGetComputationResult(req, res, handle_pacevalComputation_str);

            handle_pacevalComputation_str = null;
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

app.get('/Demo/', (req, res) =>
{
    handleGETandPOST(req, res, 'Demo', null);
});

app.post('/Demo/', (req, res) =>
{
    handleGETandPOST(req, res, null, 'Demo');
});


app.get('/health',(req,res)=> {
    res.send ("Healthiness check passed");
});

app.get('/ready',(req,res)=> {
    res.send ("Readiness check passed");
});

// Listen to the App Engine-specified port, or 8080 otherwise
const PORT = process.env.PORT || 8080;

app.listen(PORT, () =>
{
    console.log(`paceval-service listening on port ${PORT}...`);
    setTimeout(deleteComputationTimer, deleteTimeout);
    logMemoryUsed();
    if (debugEnabled == true)
        console.log(``);
});
