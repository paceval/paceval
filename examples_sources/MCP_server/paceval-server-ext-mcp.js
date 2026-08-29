#!/usr/bin/env node
"use strict";

/*
 * ============================================================================
 * paceval-server-ext-mcp.js
 * ============================================================================
 *
 * Remote MCP (Model Context Protocol) server for the paceval. REST service.
 *
 * Intended use:
 *   - SAP Joule
 *   - MCP Inspector
 *   - ChatGPT / other MCP-capable agents
 *   - Claude / Cursor / VS Code / custom MCP clients
 *
 * Architecture:
 *
 *     MCP Client / Agent
 *            |
 *            | MCP Streamable HTTP
 *            v
 *     http(s)://SERVER:8087/mcp
 *            |
 *            | HTTP REST
 *            v
 *     http://127.0.0.1:8080
 *            |
 *            v
 *         paceval.
 *
 * Default configuration:
 *
 *   paceval REST backend : http://127.0.0.1:8080
 *   MCP listen address   : 0.0.0.0
 *   MCP listen port      : 8087
 *   MCP endpoint         : /mcp
 *
 * Requirements:
 *
 *   Node.js 20 or newer.
 *
 * Install:
 *
 *   npm install @modelcontextprotocol/server @modelcontextprotocol/node zod
 *
 * Start directly:
 *
 *   node paceval-server-ext-mcp.js
 *
 * Example with PM2:
 *
 *   pm2 start ./paceval-server-ext-mcp.js \
 *       --name paceval-mcp \
 *       --node-args="--max-old-space-size=6144" \
 *       --max-memory-restart 6G
 *
 *   pm2 save
 *
 * Logs:
 *
 *   pm2 logs paceval-mcp
 *
 * Environment variables:
 *
 *   PACEVAL_URL=http://127.0.0.1:8080
 *   PACEVAL_TIMEOUT_MS=60000
 *
 *   MCP_HOST=0.0.0.0
 *   MCP_PORT=8087
 *
 *   MCP_ALLOWED_HOSTS=92.205.239.48,localhost,127.0.0.1
 *   MCP_ALLOWED_ORIGINS=92.205.239.48,localhost,127.0.0.1
 *
 * Optional authentication:
 *
 *   MCP_BEARER_TOKEN=your-secret-token
 *
 * Debug:
 *
 *   PACEVAL_MCP_DEBUG=1
 *
 *   Default is ON. Set PACEVAL_MCP_DEBUG=0 to reduce log output.
 *
 * Optional, only for deep troubleshooting:
 *
 *   PACEVAL_MCP_DEBUG_FULL=1
 *
 *   WARNING:
 *   This may print complete functions, values and handles into PM2 logs.
 *   Keep it disabled in normal operation.
 *
 * LLM / agent handle policy:
 *
 *   - Treat every paceval handle as an opaque identifier.
 *   - Preserve it exactly as returned by paceval.
 *   - Never calculate, reformat, truncate, cast, guess or invent handles.
 *   - After creating a computation, reuse its handle instead of resending
 *     the complete mathematical expression.
 *   - Prefer batch tools when one or more existing computations must be
 *     evaluated for multiple value sets.
 *
 * MCP tools exposed:
 *
 *   1. paceval_calculate
 *      REST: /Demo/
 *
 *   2. paceval_create_computation
 *      REST: /CreateComputation/
 *
 *   3. paceval_evaluate
 *      REST: /GetComputationResult/
 *
 *   4. paceval_evaluate_many
 *      REST: /GetComputationResultExt/
 *
 *   5. paceval_evaluate_multiple
 *      REST: /GetMultipleComputationsResults/
 *
 *   6. paceval_evaluate_multiple_many
 *      REST: /GetMultipleComputationsResultsExt/
 *
 *   7. paceval_get_error_information
 *      REST: /GetErrorInformation/
 *
 * IMPORTANT for the multiple-computation functions:
 *
 *   The computation handles must have been created using the same number
 *   of variables and the same declared variable names/order. A computation
 *   may leave some of those variables unused.
 *
 * Security:
 *
 *   For public production use, expose this service through HTTPS and enable
 *   appropriate authentication. The built-in bearer token is intentionally
 *   simple and useful for controlled environments / initial integration.
 *
 * ============================================================================
 */

(async () => {
    const http = require("node:http");
    const crypto = require("node:crypto");

    let McpServer;
    let createMcpHandler;
    let toNodeHandler;
    let hostHeaderValidation;
    let originValidation;
    let z;

    /*
     * ------------------------------------------------------------------------
     * Load MCP dependencies.
     *
     * Dynamic imports work reliably in a plain .js CommonJS file while still
     * supporting the ESM-first MCP SDK packages.
     * ------------------------------------------------------------------------
     */
    try {
        ({
            McpServer,
            createMcpHandler
        } = await import("@modelcontextprotocol/server"));

        ({
            toNodeHandler,
            hostHeaderValidation,
            originValidation
        } = await import("@modelcontextprotocol/node"));

        z = await import("zod/v4");
    } catch (error) {
        console.error("");
        console.error("============================================================");
        console.error("paceval MCP server: dependencies could not be loaded");
        console.error("============================================================");
        console.error("");
        console.error("Install them with:");
        console.error("");
        console.error(
            "  npm install @modelcontextprotocol/server @modelcontextprotocol/node zod"
        );
        console.error("");
        console.error(`Details: ${error.message}`);
        console.error("");
        process.exit(1);
    }

    /*
     * ------------------------------------------------------------------------
     * Configuration
     * ------------------------------------------------------------------------
     */

    const SERVICE_NAME = "paceval-mcp";
    const SERVICE_VERSION = "1.2.3";

    const INTERVAL_GUIDANCE_VERSION = "1.0";

    const PACEVAL_URL = (
        process.env.PACEVAL_URL ||
        "http://127.0.0.1:8080"
    ).replace(/\/+$/, "");

    const PACEVAL_TIMEOUT_MS =
        positiveIntegerOrDefault(
            process.env.PACEVAL_TIMEOUT_MS,
            60000
        );

    const MCP_HOST =
        process.env.MCP_HOST || "0.0.0.0";

    const MCP_PORT =
        positiveIntegerOrDefault(
            process.env.MCP_PORT,
            8087
        );

    const MCP_PATH = "/mcp";

    const DEBUG_ENABLED =
        parseBoolean(
            process.env.PACEVAL_MCP_DEBUG,
            true
        );

    const DEBUG_FULL =
        parseBoolean(
            process.env.PACEVAL_MCP_DEBUG_FULL,
            false
        );

    const MCP_BEARER_TOKEN =
        process.env.MCP_BEARER_TOKEN || "";

    const ALLOWED_HOSTS =
        parseCommaSeparatedList(
            process.env.MCP_ALLOWED_HOSTS,
            [
                "92.205.239.48",
                "localhost",
                "127.0.0.1",
                "[::1]"
            ]
        );

    const ALLOWED_ORIGINS =
        parseCommaSeparatedList(
            process.env.MCP_ALLOWED_ORIGINS,
            [
                "92.205.239.48",
                "localhost",
                "127.0.0.1",
                "[::1]"
            ]
        );

    /*
     * Official MCP Node middleware guards.
     * Entries are hostnames only, without scheme and without port.
     */
    const validateHost =
        hostHeaderValidation(ALLOWED_HOSTS);

    const validateOrigin =
        originValidation(ALLOWED_ORIGINS);

    /*
     * ------------------------------------------------------------------------
     * Configuration helpers
     * ------------------------------------------------------------------------
     */

    function positiveIntegerOrDefault(value, fallback) {
        const number =
            Number(value);

        if (
            Number.isInteger(number) &&
            number > 0
        ) {
            return number;
        }

        return fallback;
    }

    function parseBoolean(value, fallback) {
        if (
            value === undefined ||
            value === null ||
            String(value).trim() === ""
        ) {
            return fallback;
        }

        const normalized =
            String(value)
                .trim()
                .toLowerCase();

        if (
            ["1", "true", "yes", "on"].includes(
                normalized
            )
        ) {
            return true;
        }

        if (
            ["0", "false", "no", "off"].includes(
                normalized
            )
        ) {
            return false;
        }

        return fallback;
    }

    function parseCommaSeparatedList(
        value,
        fallback
    ) {
        if (
            !value ||
            !String(value).trim()
        ) {
            return fallback;
        }

        return String(value)
            .split(",")
            .map(item => item.trim())
            .filter(Boolean);
    }

    function pacevalBoolean(value) {
        return (
            value === true ||
            value === 1 ||
            value === "1" ||
            String(value).toLowerCase() === "true"
        );
    }

    /*
     * ------------------------------------------------------------------------
     * Logging
     *
     * PM2 captures console.log / console.warn / console.error. All messages
     * contain timestamps and compact event identifiers for easier filtering.
     *
     * Examples:
     *
     *   pm2 logs paceval-mcp
     *
     *   pm2 logs paceval-mcp | grep "tool.start"
     *
     *   pm2 logs paceval-mcp | grep "rest.response"
     * ------------------------------------------------------------------------
     */

    function timestamp() {
        return new Date().toISOString();
    }

    function serializeForLog(value) {
        try {
            return JSON.stringify(value);
        } catch {
            return String(value);
        }
    }

    function logInfo(event, details) {
        console.log(
            `[${timestamp()}] [${SERVICE_NAME}] [INFO] ${event}` +
            (
                details !== undefined
                    ? ` ${serializeForLog(details)}`
                    : ""
            )
        );
    }

    function logDebug(event, details) {
        if (!DEBUG_ENABLED) {
            return;
        }

        console.log(
            `[${timestamp()}] [${SERVICE_NAME}] [DEBUG] ${event}` +
            (
                details !== undefined
                    ? ` ${serializeForLog(details)}`
                    : ""
            )
        );
    }

    function logWarn(event, details) {
        console.warn(
            `[${timestamp()}] [${SERVICE_NAME}] [WARN] ${event}` +
            (
                details !== undefined
                    ? ` ${serializeForLog(details)}`
                    : ""
            )
        );
    }

    function logError(event, details) {
        console.error(
            `[${timestamp()}] [${SERVICE_NAME}] [ERROR] ${event}` +
            (
                details !== undefined
                    ? ` ${serializeForLog(details)}`
                    : ""
            )
        );
    }

    function newId(prefix) {
        return (
            `${prefix}-` +
            crypto
                .randomBytes(4)
                .toString("hex")
        );
    }

    /*
     * ------------------------------------------------------------------------
     * Safe debug summaries
     *
     * We deliberately avoid putting complete long formulas / large batches
     * into logs unless PACEVAL_MCP_DEBUG_FULL=1 was explicitly configured.
     * ------------------------------------------------------------------------
     */

    function previewText(value, maxLength = 100) {
        const text =
            String(value ?? "");

        if (
            text.length <= maxLength
        ) {
            return text;
        }

        return (
            text.slice(0, maxLength) +
            `... [${text.length} chars]`
        );
    }

    function countSeparatedValues(value) {
        if (
            value === undefined ||
            value === null ||
            String(value) === ""
        ) {
            return 0;
        }

        return String(value)
            .split(";")
            .length;
    }

    function summarizeRestParameters(parameters) {
        if (DEBUG_FULL) {
            return parameters;
        }

        const summary = {};

        for (
            const [key, value]
            of Object.entries(parameters)
        ) {
            switch (key) {
                case "functionString":
                    summary.functionStringPreview =
                        previewText(value, 120);
                    summary.functionStringLength =
                        String(value ?? "").length;
                    break;

                case "values":
                    summary.valuesCount =
                        countSeparatedValues(value);
                    break;

                case "handle_pacevalComputations":
                    summary.computationHandlesCount =
                        countSeparatedValues(value);
                    break;

                case "handle_pacevalComputation":
                    summary.handle =
                        previewText(value, 40);
                    break;

                default:
                    summary[key] =
                        value;
                    break;
            }
        }

        return summary;
    }

    function summarizeToolArguments(
        toolName,
        args
    ) {
        if (DEBUG_FULL) {
            return args;
        }

        switch (toolName) {
            case "paceval_calculate":
                return {
                    expressionPreview:
                        previewText(
                            args.expression,
                            120
                        ),

                    expressionLength:
                        args.expression.length,

                    variables:
                        args.variables,

                    valueCount:
                        args.values.length,

                    interval:
                        args.interval
                };

            case "paceval_create_computation":
                return {
                    expressionPreview:
                        previewText(
                            args.expression,
                            120
                        ),

                    expressionLength:
                        args.expression.length,

                    variables:
                        args.variables,

                    interval:
                        args.interval
                };

            case "paceval_evaluate":
                return {
                    handle:
                        previewText(
                            args.handle,
                            40
                        ),

                    valueCount:
                        args.values.length
                };

            case "paceval_evaluate_many":
                return {
                    handle:
                        previewText(
                            args.handle,
                            40
                        ),

                    calculationCount:
                        args.valueSets.length,

                    valuesPerCalculation:
                        args.valueSets.length
                            ? args.valueSets[0].length
                            : 0
                };

            case "paceval_evaluate_multiple":
                return {
                    computationCount:
                        args.handles.length,

                    valueCount:
                        args.values.length
                };

            case "paceval_evaluate_multiple_many":
                return {
                    computationCount:
                        args.handles.length,

                    calculationCount:
                        args.valueSets.length,

                    valuesPerCalculation:
                        args.valueSets.length
                            ? args.valueSets[0].length
                            : 0
                };

            case "paceval_get_error_information":
                return {
                    handle:
                        previewText(
                            args.handle,
                            40
                        )
                };

            default:
                return {};
        }
    }

    /*
     * ------------------------------------------------------------------------
     * MCP tool result helper
     * ------------------------------------------------------------------------
     */

    function toolResult(
        value,
        isError = false
    ) {
        return {
            ...(isError ? { isError: true } : {}),

            content: [
                {
                    type:
                        "text",

                    text:
                        typeof value === "string"
                            ? value
                            : JSON.stringify(
                                value,
                                null,
                                2
                            )
                }
            ]
        };
    }

    /*
     * ------------------------------------------------------------------------
     * JSON HTTP helper for / and /health
     * ------------------------------------------------------------------------
     */

    function sendJson(
        res,
        statusCode,
        value,
        extraHeaders = {}
    ) {
        const body =
            JSON.stringify(
                value,
                null,
                2
            );

        res.writeHead(
            statusCode,
            {
                "Content-Type":
                    "application/json; charset=utf-8",

                "Content-Length":
                    Buffer.byteLength(body),

                "Cache-Control":
                    "no-store",

                ...extraHeaders
            }
        );

        res.end(body);
    }

    /*
     * ------------------------------------------------------------------------
     * Optional bearer-token check
     * ------------------------------------------------------------------------
     */

    function isAuthorized(req) {
        if (!MCP_BEARER_TOKEN) {
            return true;
        }

        const authorization =
            req.headers.authorization || "";

        return (
            authorization ===
            `Bearer ${MCP_BEARER_TOKEN}`
        );
    }

    /*
     * ------------------------------------------------------------------------
     * paceval REST client
     *
     * All paceval endpoints are called using:
     *
     *   POST
     *   Content-Type: application/x-www-form-urlencoded
     *
     * Debug output contains:
     *
     *   - endpoint
     *   - request duration
     *   - HTTP status
     *   - paceval error code / hasError
     *   - number of returned results
     * ------------------------------------------------------------------------
     */

    async function callPaceval(
        endpoint,
        parameters,
        context = {}
    ) {
        const restCallId =
            newId("rest");

        const url =
            `${PACEVAL_URL}/${endpoint}/`;

        const body =
            new URLSearchParams();

        for (
            const [key, value]
            of Object.entries(parameters)
        ) {
            if (
                value === undefined ||
                value === null
            ) {
                continue;
            }

            body.set(
                key,
                String(value)
            );
        }

        const controller =
            new AbortController();

        const timeout =
            setTimeout(
                () => controller.abort(),
                PACEVAL_TIMEOUT_MS
            );

        const start =
            Date.now();

        logDebug(
            "rest.request",
            {
                restCallId,
                toolCallId:
                    context.toolCallId,
                endpoint,
                url,
                parameters:
                    summarizeRestParameters(
                        parameters
                    )
            }
        );

        let response;

        try {
            response =
                await fetch(
                    url,
                    {
                        method:
                            "POST",

                        headers: {
                            "Content-Type":
                                "application/x-www-form-urlencoded"
                        },

                        body,

                        signal:
                            controller.signal
                    }
                );
        } catch (error) {
            const durationMs =
                Date.now() - start;

            if (
                error &&
                error.name === "AbortError"
            ) {
                logError(
                    "rest.timeout",
                    {
                        restCallId,
                        endpoint,
                        durationMs,
                        timeoutMs:
                            PACEVAL_TIMEOUT_MS
                    }
                );

                throw new Error(
                    `paceval request timed out after ${PACEVAL_TIMEOUT_MS} ms: ${url}`
                );
            }

            logError(
                "rest.connection_error",
                {
                    restCallId,
                    endpoint,
                    durationMs,
                    message:
                        error.message
                }
            );

            throw new Error(
                `Cannot reach the paceval service at ${url}: ${error.message}`
            );
        } finally {
            clearTimeout(timeout);
        }

        const responseText =
            await response.text();

        const durationMs =
            Date.now() - start;

        logDebug(
            "rest.http_response",
            {
                restCallId,
                endpoint,
                httpStatus:
                    response.status,
                durationMs,
                responseBytes:
                    Buffer.byteLength(
                        responseText
                    )
            }
        );

        if (!response.ok) {
            logError(
                "rest.http_error",
                {
                    restCallId,
                    endpoint,
                    httpStatus:
                        response.status,
                    responsePreview:
                        previewText(
                            responseText,
                            500
                        )
                }
            );

            throw new Error(
                `paceval HTTP ${response.status} ${response.statusText}: ${responseText}`
            );
        }

        let data;

        try {
            data =
                JSON.parse(
                    responseText
                );
        } catch {
            logError(
                "rest.invalid_json",
                {
                    restCallId,
                    endpoint,
                    responsePreview:
                        previewText(
                            responseText,
                            500
                        )
                }
            );

            throw new Error(
                `paceval returned invalid JSON from ${endpoint}: ${responseText}`
            );
        }

        logDebug(
            "rest.response",
            {
                restCallId,
                endpoint,
                durationMs,

                errorTypeNumber:
                    data["error-type-number"],

                hasError:
                    data.hasError,

                resultCount:
                    Array.isArray(
                        data.results
                    )
                        ? data.results.length
                        : (
                            data.result !== undefined
                                ? 1
                                : 0
                        ),

                pacevalVersion:
                    data["version-number"]
            }
        );

        return data;
    }

    /*
     * ------------------------------------------------------------------------
     * Single-computation error handling
     * ------------------------------------------------------------------------
     */

    function ensurePacevalSuccess(data) {
        const errorNumber =
            data?.["error-type-number"];

        if (
            errorNumber !== undefined &&
            errorNumber !== null &&
            Number(errorNumber) !== 0
        ) {
            const error =
                new Error(
                    data["error-message"] ||
                    data["error-type"] ||
                    `paceval error ${errorNumber}`
                );

            error.pacevalData =
                data;

            throw error;
        }

        return data;
    }

    /*
     * ------------------------------------------------------------------------
     * Batch error handling
     * ------------------------------------------------------------------------
     */

    function hasBatchError(data) {
        if (
            pacevalBoolean(
                data?.hasError
            )
        ) {
            return true;
        }

        const errorNumbers =
            data?.["error-type-numbers"];

        if (
            Array.isArray(
                errorNumbers
            )
        ) {
            return errorNumbers.some(
                value =>
                    Number(value) !== 0
            );
        }

        return false;
    }

    /*
     * ------------------------------------------------------------------------
     * Common response normalization
     *
     * This deliberately keeps the original paceval result values as returned
     * by the REST service. paceval often returns numerical results as strings,
     * which preserves the server's textual numerical representation.
     * ------------------------------------------------------------------------
     */

    function normalizedHandle(value) {
        if (
            value === undefined ||
            value === null
        ) {
            return "";
        }

        return String(value);
    }

    function normalizedHandles(value) {
        if (!Array.isArray(value)) {
            return [];
        }

        return value.map(
            item =>
                normalizedHandle(item)
        );
    }

    function normalizeSingleResult(data) {
        return {
            handle:
                normalizedHandle(
                    data.handle_pacevalComputation
                ),

            result:
                data.result,

            intervalMin:
                data["interval-min-result"],

            intervalMax:
                data["interval-max-result"],

            errorNumber:
                data["error-type-number"],

            errorPosition:
                data["error-position"],

            errorType:
                data["error-type"],

            errorMessage:
                data["error-message"],

            calculationTime:
                data["time-calculate"],

            pacevalVersion:
                data["version-number"]
        };
    }

    function normalizeCreationResult(data) {
        return {
            handle:
                normalizedHandle(
                    data.handle_pacevalComputation
                ),

            functionPreview:
                data["function-10chars"],

            functionLength:
                data["function-length"],

            errorNumber:
                data["error-type-number"],

            errorPosition:
                data["error-position"],

            errorType:
                data["error-type"],

            errorMessage:
                data["error-message"],

            creationTime:
                data["time-create"] ??
                data["time-calculate"],

            pacevalVersion:
                data["version-number"]
        };
    }

    function normalizeSingleExtResult(
        data,
        fallbackHandle,
        fallbackCount
    ) {
        return {
            handle:
                normalizedHandle(
                    data.handle_pacevalComputation
                ) ||
                fallbackHandle,

            numberOfCalculations:
                data["number-of-multiple-values"] ??
                fallbackCount,

            hasError:
                hasBatchError(data),

            results:
                data.results,

            intervalMins:
                data["interval-min-results"],

            intervalMaxs:
                data["interval-max-results"],

            errorNumbers:
                data["error-type-numbers"],

            calculationTime:
                data["time-calculate"],

            pacevalVersion:
                data["version-number"]
        };
    }

    /*
     * paceval returns GetMultipleComputationsResultsExt results in
     * computation-major order:
     *
     *   computation 1 / calculation 1
     *   computation 1 / calculation 2
     *   ...
     *   computation 2 / calculation 1
     *   computation 2 / calculation 2
     *   ...
     *
     * The matrix representation makes this easier for an AI agent to consume.
     */
    function reshapeComputationMajor(
        flatValues,
        numberOfComputations,
        numberOfCalculations
    ) {
        if (!Array.isArray(flatValues)) {
            return undefined;
        }

        const expectedLength =
            numberOfComputations *
            numberOfCalculations;

        if (
            flatValues.length !==
            expectedLength
        ) {
            logWarn(
                "result.matrix_size_mismatch",
                {
                    expectedLength,
                    actualLength:
                        flatValues.length,
                    numberOfComputations,
                    numberOfCalculations
                }
            );
        }

        const matrix = [];

        for (
            let computationIndex = 0;
            computationIndex <
                numberOfComputations;
            computationIndex++
        ) {
            const start =
                computationIndex *
                numberOfCalculations;

            const end =
                start +
                numberOfCalculations;

            matrix.push(
                flatValues.slice(
                    start,
                    end
                )
            );
        }

        return matrix;
    }

    function normalizeMultipleResult(
        data,
        fallbackHandles
    ) {
        return {
            numberOfComputations:
                data["number-of-multiple-computations"] ??
                fallbackHandles.length,

            handles:
                normalizedHandles(
                    data.handle_pacevalComputations
                ).length
                    ? normalizedHandles(
                        data.handle_pacevalComputations
                    )
                    : fallbackHandles,

            hasError:
                hasBatchError(data),

            results:
                data.results,

            intervalMins:
                data["interval-min-results"],

            intervalMaxs:
                data["interval-max-results"],

            errorNumbers:
                data["error-type-numbers"],

            calculationTime:
                data["time-calculate"],

            pacevalVersion:
                data["version-number"]
        };
    }

    function normalizeMultipleExtResult(
        data,
        fallbackHandles,
        fallbackCalculationCount
    ) {
        const numberOfComputations =
            Number(
                data["number-of-multiple-computations"] ??
                fallbackHandles.length
            );

        /*
         * Different public paceval service variants have used slightly
         * different JSON field labels for this count. Accept all known labels
         * while exposing one stable MCP property.
         */
        const numberOfCalculations =
            Number(
                data["number-of-multiple-calculations"] ??
                data["number-of-multiple-values-per-computation"] ??
                data["number-of-multiple-values"] ??
                fallbackCalculationCount
            );

        const handles =
            normalizedHandles(
                data.handle_pacevalComputations
            );

        return {
            numberOfComputations,
            numberOfCalculations,

            handles:
                handles.length
                    ? handles
                    : fallbackHandles,

            hasError:
                hasBatchError(data),

            /*
             * Raw flattened arrays exactly as returned by paceval.
             */
            results:
                data.results,

            intervalMins:
                data["interval-min-results"],

            intervalMaxs:
                data["interval-max-results"],

            errorNumbers:
                data["error-type-numbers"],

            /*
             * Agent-friendly matrix views:
             *
             *   resultsByComputation[computationIndex][calculationIndex]
             */
            resultsByComputation:
                reshapeComputationMajor(
                    data.results,
                    numberOfComputations,
                    numberOfCalculations
                ),

            intervalMinsByComputation:
                reshapeComputationMajor(
                    data["interval-min-results"],
                    numberOfComputations,
                    numberOfCalculations
                ),

            intervalMaxsByComputation:
                reshapeComputationMajor(
                    data["interval-max-results"],
                    numberOfComputations,
                    numberOfCalculations
                ),

            errorNumbersByComputation:
                reshapeComputationMajor(
                    data["error-type-numbers"],
                    numberOfComputations,
                    numberOfCalculations
                ),

            calculationTime:
                data["time-calculate"],

            pacevalVersion:
                data["version-number"]
        };
    }

    /*
     * ------------------------------------------------------------------------
     * Common tool runner
     *
     * Produces consistent PM2 logs for every MCP tool invocation.
     * ------------------------------------------------------------------------
     */

    async function runTool(
        toolName,
        args,
        implementation
    ) {
        const toolCallId =
            newId("tool");

        const start =
            Date.now();

        logInfo(
            "tool.start",
            {
                toolCallId,
                toolName,
                args:
                    summarizeToolArguments(
                        toolName,
                        args
                    )
            }
        );

        try {
            const result =
                await implementation(
                    toolCallId
                );

            const durationMs =
                Date.now() - start;

            logInfo(
                "tool.success",
                {
                    toolCallId,
                    toolName,
                    durationMs
                }
            );

            return result;
        } catch (error) {
            const durationMs =
                Date.now() - start;

            logError(
                "tool.failure",
                {
                    toolCallId,
                    toolName,
                    durationMs,
                    message:
                        error.message
                }
            );

            return toolResult(
                {
                    error:
                        `${toolName} failed: ${error.message}`,

                    paceval:
                        error.pacevalData ||
                        undefined
                },
                true
            );
        }
    }

    /*
     * ------------------------------------------------------------------------
     * MCP server factory
     *
     * createMcpHandler() creates a server through this factory per request.
     * Tool registration therefore belongs inside this function.
     * ------------------------------------------------------------------------
     */

    function createPacevalMcpServer() {
        const server =
            new McpServer(
                {
                    name:
                        SERVICE_NAME,

                    version:
                        SERVICE_VERSION
                }
            );

        /*
         * ====================================================================
         * TOOL 1: paceval_calculate
         *
         * One-shot formula creation + evaluation.
         *
         * REST endpoint:
         *   POST /Demo/
         * ====================================================================
         */
        server.registerTool(
            "paceval_calculate",

            {
                title:
                    "Calculate with paceval",

                description:
                    "Evaluate a mathematical expression with the deterministic " +
                    "paceval. mathematical engine. Use this primarily for a one-time " +
                    "calculation. If repeated evaluations are expected, prefer " +
                    "paceval_create_computation followed by paceval_evaluate or " +
                    "paceval_evaluate_many. If this tool returns a handle, preserve " +
                    "that handle exactly as returned and never invent or modify it.",

                inputSchema:
                    z.object({
                        expression:
                            z.string()
                                .min(1)
                                .describe(
                                    "Mathematical expression, for example 5*x+exp(y)"
                                ),

                        variables:
                            z.array(
                                z.string().min(1)
                            )
                            .describe(
                                "Variable names in evaluation order, for example ['x','y']"
                            ),

                        values:
                            z.array(
                                z.number()
                            )
                            .describe(
                                "Variable values in the same order, for example [2.2,3.3]"
                            ),

                        interval:
                            z.boolean()
                                .default(false)
                                .describe(
                                    "Enable paceval Trusted Interval Computation when a numerically bounded result is important. This may increase computation cost. Prefer false for ordinary high-throughput calculations."
                                )
                    })
            },

            async (args) =>
                runTool(
                    "paceval_calculate",
                    args,
                    async (toolCallId) => {
                        const {
                            expression,
                            variables,
                            values,
                            interval
                        } = args;

                        /*
                         * Catch this common agent mistake before calling paceval.
                         */
                        if (
                            variables.length !==
                            values.length
                        ) {
                            logWarn(
                                "tool.validation_error",
                                {
                                    toolCallId,
                                    toolName:
                                        "paceval_calculate",
                                    reason:
                                        "variables.length != values.length",
                                    variableCount:
                                        variables.length,
                                    valueCount:
                                        values.length
                                }
                            );

                            return toolResult(
                                {
                                    error:
                                        "The number of variables must equal the number of values.",

                                    variableCount:
                                        variables.length,

                                    valueCount:
                                        values.length
                                },
                                true
                            );
                        }

                        const data =
                            ensurePacevalSuccess(
                                await callPaceval(
                                    "Demo",
                                    {
                                        functionString:
                                            expression,

                                        numberOfVariables:
                                            variables.length,

                                        variables:
                                            variables.join(";"),

                                        values:
                                            values.join(";"),

                                        interval:
                                            interval
                                                ? "yes"
                                                : "no"
                                    },
                                    {
                                        toolCallId
                                    }
                                )
                            );

                        return toolResult(
                            normalizeSingleResult(
                                data
                            )
                        );
                    }
                )
        );

        /*
         * ====================================================================
         * TOOL 2: paceval_create_computation
         *
         * Prepare one formula once and return its reusable handle.
         *
         * REST endpoint:
         *   POST /CreateComputation/
         * ====================================================================
         */
        server.registerTool(
            "paceval_create_computation",

            {
                title:
                    "Create paceval computation",

                description:
                    "Create and prepare a reusable mathematical expression in " +
                    "paceval. Returns an opaque computation handle for repeated " +
                    "evaluations with new values. Preserve the returned handle exactly " +
                    "as returned. Reuse it for later evaluations and do not resend or " +
                    "recreate the mathematical expression unless the expression or the " +
                    "declared variables actually change. Never invent, calculate, cast, " +
                    "truncate or otherwise modify a paceval handle.",

                inputSchema:
                    z.object({
                        expression:
                            z.string()
                                .min(1)
                                .describe(
                                    "Mathematical expression to prepare"
                                ),

                        variables:
                            z.array(
                                z.string().min(1)
                            )
                            .describe(
                                "Variable names in evaluation order"
                            ),

                        interval:
                            z.boolean()
                                .default(false)
                                .describe(
                                    "Enable paceval Trusted Interval Computation when a numerically bounded result is important. This may increase computation cost. Prefer false for ordinary high-throughput calculations."
                                )
                    })
            },

            async (args) =>
                runTool(
                    "paceval_create_computation",
                    args,
                    async (toolCallId) => {
                        const {
                            expression,
                            variables,
                            interval
                        } = args;

                        const data =
                            ensurePacevalSuccess(
                                await callPaceval(
                                    "CreateComputation",
                                    {
                                        functionString:
                                            expression,

                                        numberOfVariables:
                                            variables.length,

                                        variables:
                                            variables.join(";"),

                                        interval:
                                            interval
                                                ? "yes"
                                                : "no"
                                    },
                                    {
                                        toolCallId
                                    }
                                )
                            );

                        return toolResult(
                            normalizeCreationResult(
                                data
                            )
                        );
                    }
                )
        );

        /*
         * ====================================================================
         * TOOL 3: paceval_evaluate
         *
         * Evaluate one previously created computation once.
         *
         * REST endpoint:
         *   POST /GetComputationResult/
         * ====================================================================
         */
        server.registerTool(
            "paceval_evaluate",

            {
                title:
                    "Evaluate paceval computation",

                description:
                    "Evaluate an existing paceval computation using exactly the opaque " +
                    "handle returned previously by paceval_create_computation or " +
                    "paceval_calculate. Do not resend the expression. Never invent, " +
                    "modify or numerically transform the handle. Use this for one new " +
                    "value set; for two or more value sets prefer paceval_evaluate_many.",

                inputSchema:
                    z.object({
                        handle:
                            z.string()
                                .min(1)
                                .describe(
                                    "Opaque paceval computation handle"
                                ),

                        values:
                            z.array(
                                z.number()
                            )
                            .describe(
                                "Variable values in the same order used when the computation was created"
                            )
                    })
            },

            async (args) =>
                runTool(
                    "paceval_evaluate",
                    args,
                    async (toolCallId) => {
                        const {
                            handle,
                            values
                        } = args;

                        const data =
                            ensurePacevalSuccess(
                                await callPaceval(
                                    "GetComputationResult",
                                    {
                                        handle_pacevalComputation:
                                            handle,

                                        values:
                                            values.join(";")
                                    },
                                    {
                                        toolCallId
                                    }
                                )
                            );

                        return toolResult(
                            normalizeSingleResult(
                                data
                            )
                        );
                    }
                )
        );

        /*
         * ====================================================================
         * TOOL 4: paceval_evaluate_many
         *
         * One computation × many value sets.
         *
         * REST endpoint:
         *   POST /GetComputationResultExt/
         *
         * Input:
         *
         *   valueSets = [
         *      [x1, y1],
         *      [x2, y2],
         *      [x3, y3]
         *   ]
         *
         * REST values:
         *
         *   x1;y1;x2;y2;x3;y3
         * ====================================================================
         */
        server.registerTool(
            "paceval_evaluate_many",

            {
                title:
                    "Evaluate many with paceval",

                description:
                    "Evaluate one existing paceval computation for multiple sets " +
                    "of variable values in a single request. Use exactly the previously " +
                    "returned handle and do not resend the mathematical expression. " +
                    "Prefer this tool over repeated paceval_evaluate calls whenever the " +
                    "same computation is evaluated for two or more value sets.",

                inputSchema:
                    z.object({
                        handle:
                            z.string()
                                .min(1)
                                .describe(
                                    "Opaque paceval computation handle"
                                ),

                        valueSets:
                            z.array(
                                z.array(
                                    z.number()
                                )
                            )
                            .min(1)
                            .describe(
                                "Value sets, for example [[0.5,2],[0.4,2],[0.3,2]]"
                            )
                    })
            },

            async (args) =>
                runTool(
                    "paceval_evaluate_many",
                    args,
                    async (toolCallId) => {
                        const {
                            handle,
                            valueSets
                        } = args;

                        const width =
                            valueSets[0].length;

                        for (
                            let index = 0;
                            index <
                                valueSets.length;
                            index++
                        ) {
                            if (
                                valueSets[index].length !==
                                width
                            ) {
                                return toolResult(
                                    {
                                        error:
                                            "Every value set must contain the same number of values.",

                                        expectedValuesPerSet:
                                            width,

                                        invalidSetIndex:
                                            index,

                                        actualValues:
                                            valueSets[index].length
                                    },
                                    true
                                );
                            }
                        }

                        const data =
                            await callPaceval(
                                "GetComputationResultExt",
                                {
                                    handle_pacevalComputation:
                                        handle,

                                    numberOfCalculations:
                                        valueSets.length,

                                    values:
                                        valueSets
                                            .flat()
                                            .join(";")
                                },
                                {
                                    toolCallId
                                }
                            );

                        return toolResult(
                            normalizeSingleExtResult(
                                data,
                                handle,
                                valueSets.length
                            ),
                            hasBatchError(
                                data
                            )
                        );
                    }
                )
        );

        /*
         * ====================================================================
         * TOOL 5: paceval_evaluate_multiple
         *
         * Many computations × one common value set.
         *
         * REST endpoint:
         *   POST /GetMultipleComputationsResults/
         *
         * IMPORTANT:
         * All handles must use the same number of declared variables and the
         * same variable names/order.
         *
         * REST parameters:
         *
         *   handle_pacevalComputations
         *   numberOfpacevalComputations
         *   values
         * ====================================================================
         */
        server.registerTool(
            "paceval_evaluate_multiple",

            {
                title:
                    "Evaluate multiple paceval computations",

                description:
                    "Evaluate multiple existing paceval computations in parallel " +
                    "using one common set of variable values. Pass only the exact " +
                    "previously returned computation handles; do not resend the original " +
                    "expressions and never invent or modify handles. All computations " +
                    "must have been created with the same number and order of declared " +
                    "variables.",

                inputSchema:
                    z.object({
                        handles:
                            z.array(
                                z.string().min(1)
                            )
                            .min(1)
                            .describe(
                                "paceval computation handles"
                            ),

                        values:
                            z.array(
                                z.number()
                            )
                            .describe(
                                "One common value set for all computations"
                            )
                    })
            },

            async (args) =>
                runTool(
                    "paceval_evaluate_multiple",
                    args,
                    async (toolCallId) => {
                        const {
                            handles,
                            values
                        } = args;

                        const data =
                            await callPaceval(
                                "GetMultipleComputationsResults",
                                {
                                    handle_pacevalComputations:
                                        handles.join(";"),

                                    numberOfpacevalComputations:
                                        handles.length,

                                    values:
                                        values.join(";")
                                },
                                {
                                    toolCallId
                                }
                            );

                        return toolResult(
                            normalizeMultipleResult(
                                data,
                                handles
                            ),
                            hasBatchError(
                                data
                            )
                        );
                    }
                )
        );

        /*
         * ====================================================================
         * TOOL 6: paceval_evaluate_multiple_many
         *
         * Many computations × many value sets.
         *
         * REST endpoint:
         *   POST /GetMultipleComputationsResultsExt/
         *
         * This is the most powerful bulk-evaluation path exposed by this MCP
         * adapter.
         *
         * IMPORTANT:
         * All handles must use the same number of declared variables and the
         * same variable names/order.
         *
         * Example:
         *
         *   handles = [f1, f2]
         *
         *   valueSets = [
         *       [2.6, 5.8],
         *       [-1.2, 6.9],
         *       [-1.8, 12.1]
         *   ]
         *
         * REST values:
         *
         *   2.6;5.8;-1.2;6.9;-1.8;12.1
         *
         * REST parameters:
         *
         *   handle_pacevalComputations
         *   numberOfpacevalComputations
         *   numberOfCalculations
         *   values
         *
         * paceval returns flattened arrays in computation-major order.
         * This MCP tool also adds matrix views for easier agent consumption.
         * ====================================================================
         */
        server.registerTool(
            "paceval_evaluate_multiple_many",

            {
                title:
                    "Evaluate multiple computations for many value sets",

                description:
                    "Evaluate multiple existing paceval computations for multiple " +
                    "sets of variable values in one bulk request. Pass only the exact " +
                    "previously returned computation handles and do not resend the " +
                    "corresponding mathematical expressions. Never invent or modify a " +
                    "handle. Prefer this tool instead of many individual calls when " +
                    "multiple computations must be evaluated across multiple scenarios. " +
                    "All computations must use the same declared variables in the same order.",

                inputSchema:
                    z.object({
                        handles:
                            z.array(
                                z.string().min(1)
                            )
                            .min(1)
                            .describe(
                                "paceval computation handles"
                            ),

                        valueSets:
                            z.array(
                                z.array(
                                    z.number()
                                )
                            )
                            .min(1)
                            .describe(
                                "Value sets, for example [[2.6,5.8],[-1.2,6.9],[-1.8,12.1]]"
                            )
                    })
            },

            async (args) =>
                runTool(
                    "paceval_evaluate_multiple_many",
                    args,
                    async (toolCallId) => {
                        const {
                            handles,
                            valueSets
                        } = args;

                        const width =
                            valueSets[0].length;

                        for (
                            let index = 0;
                            index <
                                valueSets.length;
                            index++
                        ) {
                            if (
                                valueSets[index].length !==
                                width
                            ) {
                                return toolResult(
                                    {
                                        error:
                                            "Every value set must contain the same number of values.",

                                        expectedValuesPerSet:
                                            width,

                                        invalidSetIndex:
                                            index,

                                        actualValues:
                                            valueSets[index].length
                                    },
                                    true
                                );
                            }
                        }

                        const data =
                            await callPaceval(
                                "GetMultipleComputationsResultsExt",
                                {
                                    handle_pacevalComputations:
                                        handles.join(";"),

                                    numberOfpacevalComputations:
                                        handles.length,

                                    numberOfCalculations:
                                        valueSets.length,

                                    values:
                                        valueSets
                                            .flat()
                                            .join(";")
                                },
                                {
                                    toolCallId
                                }
                            );

                        return toolResult(
                            normalizeMultipleExtResult(
                                data,
                                handles,
                                valueSets.length
                            ),
                            hasBatchError(
                                data
                            )
                        );
                    }
                )
        );

        /*
         * ====================================================================
         * TOOL 7: paceval_get_error_information
         *
         * Explicit diagnostic information for one computation handle.
         *
         * REST endpoint:
         *   POST /GetErrorInformation/
         * ====================================================================
         */
        server.registerTool(
            "paceval_get_error_information",

            {
                title:
                    "Get paceval error information",

                description:
                    "Retrieve detailed paceval error information for an existing " +
                    "computation handle. Use exactly the handle returned by paceval. " +
                    "Useful for diagnostics after a failed creation or evaluation. " +
                    "Never invent or modify the handle.",

                inputSchema:
                    z.object({
                        handle:
                            z.string()
                                .min(1)
                                .describe(
                                    "Opaque paceval computation handle"
                                )
                    })
            },

            async (args) =>
                runTool(
                    "paceval_get_error_information",
                    args,
                    async (toolCallId) => {
                        const {
                            handle
                        } = args;

                        const data =
                            await callPaceval(
                                "GetErrorInformation",
                                {
                                    handle_pacevalComputation:
                                        handle
                                },
                                {
                                    toolCallId
                                }
                            );

                        return toolResult(
                            {
                                handle:
                                    normalizedHandle(
                                        data.handle_pacevalComputation
                                    ) ||
                                    handle,

                                hasError:
                                    pacevalBoolean(
                                        data.hasError
                                    ),

                                errorNumber:
                                    data["error-type-number"],

                                errorPosition:
                                    data["error-position"],

                                errorOperator:
                                    data["error-operator"],

                                errorType:
                                    data["error-type"],

                                errorMessage:
                                    data["error-message"],

                                pacevalVersion:
                                    data["version-number"]
                            },
                            pacevalBoolean(
                                data.hasError
                            )
                        );
                    }
                )
        );

        return server;
    }

    /*
     * ------------------------------------------------------------------------
     * MCP Streamable HTTP handler
     *
     * Current MCP SDK v2 architecture:
     *
     *   createMcpHandler(factory)
     *          |
     *          v
     *   toNodeHandler(handler)
     *
     * createMcpHandler's default legacy fallback keeps stateless 2025-era
     * Streamable HTTP clients compatible as well.
     * ------------------------------------------------------------------------
     */

    const mcpHandler =
        createMcpHandler(
            () =>
                createPacevalMcpServer()
        );

    const nodeMcpHandler =
        toNodeHandler(
            mcpHandler,
            {
                onerror(error) {
                    logError(
                        "mcp.handler_error",
                        {
                            message:
                                error?.message ||
                                String(error),

                            stack:
                                DEBUG_ENABLED
                                    ? error?.stack
                                    : undefined
                        }
                    );
                }
            }
        );

    /*
     * ------------------------------------------------------------------------
     * HTTP server
     * ------------------------------------------------------------------------
     */

    const httpServer =
        http.createServer(
            async (req, res) => {
                const requestId =
                    newId("http");

                const requestStart =
                    Date.now();

                const remoteAddress =
                    req.socket?.remoteAddress ||
                    "";

                let requestUrl;

                try {
                    requestUrl =
                        new URL(
                            req.url || "/",
                            `http://${req.headers.host || "localhost"}`
                        );
                } catch {
                    logWarn(
                        "http.invalid_url",
                        {
                            requestId,
                            method:
                                req.method,
                            url:
                                req.url
                        }
                    );

                    return sendJson(
                        res,
                        400,
                        {
                            error:
                                "Invalid request URL"
                        }
                    );
                }

                logDebug(
                    "http.request",
                    {
                        requestId,
                        method:
                            req.method,
                        path:
                            requestUrl.pathname,
                        host:
                            req.headers.host,
                        origin:
                            req.headers.origin,
                        remoteAddress
                    }
                );

                /*
                 * Log response status and total HTTP duration after completion.
                 */
                res.once(
                    "finish",
                    () => {
                        logDebug(
                            "http.response",
                            {
                                requestId,
                                method:
                                    req.method,
                                path:
                                    requestUrl.pathname,
                                statusCode:
                                    res.statusCode,
                                durationMs:
                                    Date.now() -
                                    requestStart
                            }
                        );
                    }
                );

                /*
                 * Human-readable service status.
                 */
                if (
                    requestUrl.pathname === "/"
                ) {
                    return sendJson(
                        res,
                        200,
                        {
                            service:
                                "paceval MCP Server",

                            version:
                                SERVICE_VERSION,

                            status:
                                "running",

                            protocol:
                                "MCP Streamable HTTP",

                            mcpEndpoint:
                                MCP_PATH,

                            healthEndpoint:
                                "/health",

                            pacevalBackend:
                                PACEVAL_URL,

                            tools: [
                                "paceval_calculate",
                                "paceval_create_computation",
                                "paceval_evaluate",
                                "paceval_evaluate_many",
                                "paceval_evaluate_multiple",
                                "paceval_evaluate_multiple_many",
                                "paceval_get_error_information"
                            ]
                        }
                    );
                }

                /*
                 * Lightweight process health endpoint.
                 *
                 * It confirms that this MCP process is running and configured.
                 * It does not intentionally execute a paceval computation.
                 */
                if (
                    requestUrl.pathname ===
                    "/health"
                ) {
                    return sendJson(
                        res,
                        200,
                        {
                            status:
                                "ok",

                            service:
                                SERVICE_NAME,

                            version:
                                SERVICE_VERSION,

                            mcpHost:
                                MCP_HOST,

                            mcpPort:
                                MCP_PORT,

                            mcpEndpoint:
                                MCP_PATH,

                            pacevalBackend:
                                PACEVAL_URL,

                            debug:
                                DEBUG_ENABLED,

                            authentication:
                                MCP_BEARER_TOKEN
                                    ? "bearer-token"
                                    : "disabled",

                            toolsCount:
                                7
                        }
                    );
                }

                /*
                 * Only /mcp is the MCP endpoint.
                 */
                if (
                    requestUrl.pathname !==
                    MCP_PATH
                ) {
                    return sendJson(
                        res,
                        404,
                        {
                            error:
                                "Not found",

                            mcpEndpoint:
                                MCP_PATH
                        }
                    );
                }

                /*
                 * Official MCP Host header guard.
                 * Protects against DNS rebinding.
                 */
                if (
                    !validateHost(
                        req,
                        res
                    )
                ) {
                    logWarn(
                        "security.host_rejected",
                        {
                            requestId,
                            host:
                                req.headers.host
                        }
                    );

                    return;
                }

                /*
                 * Official MCP Origin guard.
                 *
                 * Requests without Origin are allowed, as expected for normal
                 * server-to-server MCP clients. Browser requests with an Origin
                 * must match the allowlist.
                 */
                if (
                    !validateOrigin(
                        req,
                        res
                    )
                ) {
                    logWarn(
                        "security.origin_rejected",
                        {
                            requestId,
                            origin:
                                req.headers.origin
                        }
                    );

                    return;
                }

                /*
                 * Add CORS response headers only for an explicitly accepted
                 * browser Origin. This is helpful for browser-based inspectors.
                 */
                if (
                    req.headers.origin
                ) {
                    res.setHeader(
                        "Access-Control-Allow-Origin",
                        req.headers.origin
                    );

                    res.setHeader(
                        "Vary",
                        "Origin"
                    );
                }

                /*
                 * Optional simple bearer-token protection.
                 */
                if (
                    !isAuthorized(req)
                ) {
                    logWarn(
                        "security.authentication_failed",
                        {
                            requestId,
                            remoteAddress
                        }
                    );

                    return sendJson(
                        res,
                        401,
                        {
                            jsonrpc:
                                "2.0",

                            error: {
                                code:
                                    -32001,

                                message:
                                    "Unauthorized"
                            },

                            id:
                                null
                        },
                        {
                            "WWW-Authenticate":
                                "Bearer"
                        }
                    );
                }

                /*
                 * Browser preflight support.
                 */
                if (
                    req.method === "OPTIONS"
                ) {
                    res.writeHead(
                        204,
                        {
                            "Access-Control-Allow-Methods":
                                "POST, GET, DELETE, OPTIONS",

                            "Access-Control-Allow-Headers":
                                "Content-Type, Accept, Authorization, MCP-Protocol-Version, MCP-Session-Id",

                            "Access-Control-Max-Age":
                                "86400"
                        }
                    );

                    return res.end();
                }

                /*
                 * Forward the request to the official MCP Node adapter.
                 */
                try {
                    await nodeMcpHandler(
                        req,
                        res
                    );
                } catch (error) {
                    logError(
                        "http.mcp_dispatch_error",
                        {
                            requestId,
                            message:
                                error?.message ||
                                String(error),

                            stack:
                                DEBUG_ENABLED
                                    ? error?.stack
                                    : undefined
                        }
                    );

                    if (
                        !res.headersSent
                    ) {
                        return sendJson(
                            res,
                            500,
                            {
                                jsonrpc:
                                    "2.0",

                                error: {
                                    code:
                                        -32603,

                                    message:
                                        "Internal MCP server error"
                                },

                                id:
                                    null
                            }
                        );
                    }

                    if (
                        !res.writableEnded
                    ) {
                        res.end();
                    }
                }
            }
        );

    /*
     * ------------------------------------------------------------------------
     * Low-level HTTP client errors
     * ------------------------------------------------------------------------
     */

    httpServer.on(
        "clientError",
        (error, socket) => {
            logWarn(
                "http.client_error",
                {
                    message:
                        error.message
                }
            );

            if (
                socket.writable
            ) {
                socket.end(
                    "HTTP/1.1 400 Bad Request\r\n\r\n"
                );
            }
        }
    );

    /*
     * ------------------------------------------------------------------------
     * Start
     * ------------------------------------------------------------------------
     */

    httpServer.listen(
        MCP_PORT,
        MCP_HOST,
        () => {
            console.log("");
            console.log("============================================================");
            console.log("paceval MCP server is running");
            console.log("============================================================");
            console.log(`Version           : ${SERVICE_VERSION}`);
            console.log(`Node.js           : ${process.version}`);
            console.log(`PID               : ${process.pid}`);
            console.log(`MCP bind address  : ${MCP_HOST}`);
            console.log(`MCP port          : ${MCP_PORT}`);
            console.log(`MCP path          : ${MCP_PATH}`);
            console.log(`paceval backend   : ${PACEVAL_URL}`);
            console.log(`paceval timeout   : ${PACEVAL_TIMEOUT_MS} ms`);
            console.log(`Debug             : ${DEBUG_ENABLED ? "enabled" : "disabled"}`);
            console.log(`Debug full data   : ${DEBUG_FULL ? "enabled" : "disabled"}`);
            console.log(`Allowed hosts     : ${ALLOWED_HOSTS.join(", ")}`);
            console.log(`Allowed origins   : ${ALLOWED_ORIGINS.join(", ")}`);
            console.log(
                `Authentication    : ${
                    MCP_BEARER_TOKEN
                        ? "Bearer token enabled"
                        : "disabled"
                }`
            );
            console.log("------------------------------------------------------------");
            console.log("Tools:");
            console.log("  1. paceval_calculate");
            console.log("  2. paceval_create_computation");
            console.log("  3. paceval_evaluate");
            console.log("  4. paceval_evaluate_many");
            console.log("  5. paceval_evaluate_multiple");
            console.log("  6. paceval_evaluate_multiple_many");
            console.log("  7. paceval_get_error_information");
            console.log("------------------------------------------------------------");
            console.log(
                `Local health      : http://127.0.0.1:${MCP_PORT}/health`
            );
            console.log(
                `Local MCP         : http://127.0.0.1:${MCP_PORT}${MCP_PATH}`
            );
            console.log("============================================================");
            console.log("");

            logInfo(
                "server.started",
                {
                    version:
                        SERVICE_VERSION,
                    node:
                        process.version,
                    pid:
                        process.pid,
                    mcpHost:
                        MCP_HOST,
                    mcpPort:
                        MCP_PORT,
                    pacevalBackend:
                        PACEVAL_URL,
                    toolsCount:
                        7
                }
            );
        }
    );

    /*
     * ------------------------------------------------------------------------
     * Graceful shutdown
     * ------------------------------------------------------------------------
     */

    let shuttingDown =
        false;

    async function shutdown(signal) {
        if (shuttingDown) {
            return;
        }

        shuttingDown =
            true;

        logInfo(
            "server.shutdown",
            {
                signal
            }
        );

        httpServer.close();

        try {
            if (
                mcpHandler &&
                typeof mcpHandler.close ===
                    "function"
            ) {
                await mcpHandler.close();
            }
        } catch (error) {
            logError(
                "server.shutdown_handler_error",
                {
                    message:
                        error.message
                }
            );
        }

        setTimeout(
            () => process.exit(0),
            250
        );
    }

    process.on(
        "SIGINT",
        () => shutdown("SIGINT")
    );

    process.on(
        "SIGTERM",
        () => shutdown("SIGTERM")
    );

    process.on(
        "uncaughtException",
        (error) => {
            logError(
                "process.uncaught_exception",
                {
                    message:
                        error.message,
                    stack:
                        error.stack
                }
            );
        }
    );

    process.on(
        "unhandledRejection",
        (reason) => {
            logError(
                "process.unhandled_rejection",
                {
                    reason:
                        reason instanceof Error
                            ? {
                                message:
                                    reason.message,
                                stack:
                                    reason.stack
                            }
                            : String(reason)
                }
            );
        }
    );
})();
