package com.tdfraud.controller;

// FraudAlertController.java
// TD Financial Crime Analytics — Spring Boot REST API
//
// Demonstrates Java/Spring Boot skills for:
//   - Associate Software Engineer L3 (TD Technology Solutions)
//   - Associate Engineer I (TD Technology Solutions)
//
// Exposes the AML analytics pipeline as a RESTful API that an
// Angular frontend (or any consumer) can call.
//
// Patterns demonstrated:
//   - @RestController with proper HTTP verb mapping
//   - @RequestParam with validation and defaults
//   - @PathVariable for resource-based URLs
//   - ResponseEntity for HTTP status control
//   - Service layer separation (controller never touches data directly)
//   - DTO pattern for response shaping
//   - @CrossOrigin for Angular local dev
//   - Proper error handling with @ExceptionHandler

import com.tdfraud.dto.AlertSummaryDto;
import com.tdfraud.dto.RiskScoreDto;
import com.tdfraud.dto.TransactionDto;
import com.tdfraud.dto.AmlKpiDto;
import com.tdfraud.service.FraudAnalyticsService;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

import java.util.List;
import java.util.Map;

@RestController
@RequestMapping("/api/v1/fraud")
@CrossOrigin(origins = {"http://localhost:4200", "https://td-fraud-analytics.lovable.app"})
public class FraudAlertController {

    private final FraudAnalyticsService analyticsService;

    // Constructor injection — preferred over @Autowired field injection
    public FraudAlertController(FraudAnalyticsService analyticsService) {
        this.analyticsService = analyticsService;
    }

    // ── GET /api/v1/fraud/kpis ─────────────────────────────────────────────
    // Dashboard KPIs — total alerts, escalation rate, avg amount, high value count
    @GetMapping("/kpis")
    public ResponseEntity<AmlKpiDto> getKpis() {
        AmlKpiDto kpis = analyticsService.computeKpis();
        return ResponseEntity.ok(kpis);
    }

    // ── GET /api/v1/fraud/transactions ─────────────────────────────────────
    // Paginated transaction list with optional filters
    //
    // Query params:
    //   page         (default 0)
    //   size         (default 25, max 100)
    //   flaggedOnly  (default false)
    //   minAmount    (optional)
    //   type         (optional — Wire Transfer, Cash Deposit, etc.)
    @GetMapping("/transactions")
    public ResponseEntity<Map<String, Object>> getTransactions(
            @RequestParam(defaultValue = "0")    int     page,
            @RequestParam(defaultValue = "25")   int     size,
            @RequestParam(defaultValue = "false") boolean flaggedOnly,
            @RequestParam(required = false)      Double  minAmount,
            @RequestParam(required = false)      String  type
    ) {
        // Cap page size to prevent expensive queries
        int cappedSize = Math.min(size, 100);

        List<TransactionDto> transactions = analyticsService.getTransactions(
            page, cappedSize, flaggedOnly, minAmount, type
        );
        long totalCount = analyticsService.countTransactions(flaggedOnly, minAmount, type);

        Map<String, Object> response = Map.of(
            "data",        transactions,
            "page",        page,
            "size",        cappedSize,
            "total",       totalCount,
            "totalPages",  (int) Math.ceil((double) totalCount / cappedSize)
        );

        return ResponseEntity.ok(response);
    }

    // ── GET /api/v1/fraud/transactions/{transactionId} ─────────────────────
    // Single transaction detail with full audit trail
    @GetMapping("/transactions/{transactionId}")
    public ResponseEntity<TransactionDto> getTransaction(
            @PathVariable String transactionId
    ) {
        return analyticsService.findTransaction(transactionId)
            .map(ResponseEntity::ok)
            .orElse(ResponseEntity.notFound().build());
    }

    // ── GET /api/v1/fraud/alerts ───────────────────────────────────────────
    // Alert queue — paginated, filterable by status and flag reason
    @GetMapping("/alerts")
    public ResponseEntity<List<AlertSummaryDto>> getAlerts(
            @RequestParam(required = false) String status,
            @RequestParam(required = false) String flagReason,
            @RequestParam(defaultValue = "0") int page,
            @RequestParam(defaultValue = "50") int size
    ) {
        List<AlertSummaryDto> alerts = analyticsService.getAlerts(
            status, flagReason, page, Math.min(size, 100)
        );
        return ResponseEntity.ok(alerts);
    }

    // ── GET /api/v1/fraud/risk-scores ──────────────────────────────────────
    // Customer risk scores — sorted by composite score descending
    //
    // Query params:
    //   tier      (Low / Medium / High / Critical — optional filter)
    //   segment   (Retail / Small Business / Commercial / Wealth — optional)
    //   minScore  (optional floor)
    @GetMapping("/risk-scores")
    public ResponseEntity<List<RiskScoreDto>> getRiskScores(
            @RequestParam(required = false) String tier,
            @RequestParam(required = false) String segment,
            @RequestParam(required = false) Double minScore
    ) {
        List<RiskScoreDto> scores = analyticsService.getRiskScores(
            tier, segment, minScore
        );
        return ResponseEntity.ok(scores);
    }

    // ── GET /api/v1/fraud/risk-scores/{customerId} ─────────────────────────
    // Individual customer risk profile with score breakdown
    @GetMapping("/risk-scores/{customerId}")
    public ResponseEntity<RiskScoreDto> getCustomerRiskScore(
            @PathVariable String customerId
    ) {
        return analyticsService.getCustomerRiskScore(customerId)
            .map(ResponseEntity::ok)
            .orElse(ResponseEntity.notFound().build());
    }

    // ── GET /api/v1/fraud/structuring ──────────────────────────────────────
    // Structuring suspects — customers with multiple near-threshold cash txns
    @GetMapping("/structuring")
    public ResponseEntity<List<Map<String, Object>>> getStructuringSuspects() {
        List<Map<String, Object>> suspects = analyticsService.detectStructuring();
        return ResponseEntity.ok(suspects);
    }

    // ── GET /api/v1/fraud/jurisdiction-exposure ────────────────────────────
    // Transaction volume by counterparty country with high-risk flags
    @GetMapping("/jurisdiction-exposure")
    public ResponseEntity<List<Map<String, Object>>> getJurisdictionExposure() {
        return ResponseEntity.ok(analyticsService.getJurisdictionExposure());
    }

    // ── GET /api/v1/fraud/monthly-trends ──────────────────────────────────
    // Monthly transaction volume and flag rate — for dashboard charts
    @GetMapping("/monthly-trends")
    public ResponseEntity<List<Map<String, Object>>> getMonthlyTrends(
            @RequestParam(defaultValue = "2024") int year
    ) {
        return ResponseEntity.ok(analyticsService.getMonthlyTrends(year));
    }

    // ── Exception handling ─────────────────────────────────────────────────

    @ExceptionHandler(IllegalArgumentException.class)
    public ResponseEntity<Map<String, String>> handleBadRequest(
            IllegalArgumentException ex
    ) {
        return ResponseEntity
            .status(HttpStatus.BAD_REQUEST)
            .body(Map.of("error", ex.getMessage()));
    }

    @ExceptionHandler(Exception.class)
    public ResponseEntity<Map<String, String>> handleGenericError(Exception ex) {
        return ResponseEntity
            .status(HttpStatus.INTERNAL_SERVER_ERROR)
            .body(Map.of("error", "An unexpected error occurred",
                         "detail", ex.getMessage()));
    }
}
