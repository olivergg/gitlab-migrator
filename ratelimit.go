package main

import (
	"context"
	"net/http"
	"strings"
	"time"

	"github.com/hashicorp/go-hclog"
	"golang.org/x/time/rate"
)

var _ http.RoundTripper = &rateLimitedTransport{}

type rateLimitedTransport struct {
	base           http.RoundTripper
	coreLimiter    *rate.Limiter
	searchLimiter  *rate.Limiter
	writeLimiter   *rate.Limiter // Separate limiter for POST/PATCH to prevent secondary rate limits
	logger         hclog.Logger
}

func newRateLimitedTransport(base http.RoundTripper) *rateLimitedTransport {
	// GitHub limits:
	// - Core API: 5000 requests per hour = ~83 req/min = ~1.38 req/sec
	// - Search API: 30 requests per minute = 0.5 req/sec
	// - Secondary rate limit: Content creation is aggressively rate limited to prevent abuse
	//
	// We set limits well below the actual limits for safety margin:
	// - Core (GET/etc): 0.8 req/sec (48 req/min, ~2880 req/hour) - 42% margin
	// - Search: 0.25 req/sec (15 req/min) - 50% margin
	// - Write (POST/PATCH): 0.1 req/sec (6 req/min) - Very conservative to avoid secondary limits
	//
	// Separate write limiter prevents GitHub's secondary rate limit on content creation

	return &rateLimitedTransport{
		base:           base,
		coreLimiter:    rate.NewLimiter(rate.Limit(0.33), 1),  // 0.33 req/sec (3 per 10 sec) for reads
		searchLimiter:  rate.NewLimiter(rate.Limit(0.1), 1),  // 0.1 req/sec (1 per 10 sec) for search
		writeLimiter:   rate.NewLimiter(rate.Limit(0.033), 1), // 0.033 req/sec (1 every ~30 sec) - very conservative for content creation
		logger:         logger,
	}
}

func (r *rateLimitedTransport) RoundTrip(req *http.Request) (*http.Response, error) {
	// Determine which rate limiter to use based on request method and URL
	var limiter *rate.Limiter
	var limiterType string

	// Write operations (POST, PATCH, PUT, DELETE) use write limiter to avoid secondary rate limits
	if req.Method == http.MethodPost || req.Method == http.MethodPatch ||
	   req.Method == http.MethodPut || req.Method == http.MethodDelete {
		limiter = r.writeLimiter
		limiterType = "write"
	} else if req.URL != nil && strings.Contains(req.URL.Path, "/search/") {
		// Search API endpoint
		limiter = r.searchLimiter
		limiterType = "search"
	} else {
		// Core API endpoint (GET, HEAD, etc.)
		limiter = r.coreLimiter
		limiterType = "core"
	}

	// Wait for rate limiter token before making the request
	if err := limiter.Wait(context.Background()); err != nil {
		return nil, err
	}

	// Log the operation being rate limited
	r.logger.Trace("rate limiting request",
		"method", req.Method,
		"url_path", req.URL.Path,
		"limiter_type", limiterType)

	// Add additional delay for write operations to avoid secondary rate limit
	if limiter == r.writeLimiter {
		time.Sleep(1 * time.Second)
	} else if limiter == r.searchLimiter {
		time.Sleep(500 * time.Millisecond)
	} else {
		time.Sleep(200 * time.Millisecond)
	}

	return r.base.RoundTrip(req)
}
