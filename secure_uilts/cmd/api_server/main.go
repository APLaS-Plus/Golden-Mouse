package main

import (
	"encoding/json"
	"fmt"
	"log"
	"net/http"
	"secure_utils"
)

// Server 全局服务器结构 (简化版)
type Server struct {
	dlp        *secure_utils.SmartDLP
	firewall   *secure_utils.DBFirewall
	summarizer *secure_utils.ContentSummarizer
	client     *secure_utils.DeepSeekClient // 用于查余额
}

// JSONResponse 通用 JSON 响应
type JSONResponse struct {
	Code    int         `json:"code"`
	Message string      `json:"message,omitempty"`
	Data    interface{} `json:"data,omitempty"`
}

func sendJSON(w http.ResponseWriter, code int, data interface{}) {
	w.Header().Set("Content-Type", "application/json")
	w.WriteHeader(code)
	json.NewEncoder(w).Encode(JSONResponse{
		Code: code,
		Data: data,
	})
}

func sendError(w http.ResponseWriter, code int, message string) {
	w.Header().Set("Content-Type", "application/json")
	w.WriteHeader(code)
	json.NewEncoder(w).Encode(JSONResponse{
		Code:    code,
		Message: message,
	})
}

func main() {
	// 1. 加载 API Key
	apiKey, err := secure_utils.LoadAPIKey()
	if err != nil {
		log.Fatal("无法加载 API Key: ", err)
	}

	// 2. 初始化客户端
	client, err := secure_utils.NewDeepSeekClient(apiKey)
	if err != nil {
		log.Fatal("初始化客户端失败: ", err)
	}

	// 3. 初始化组件
	srv := &Server{
		dlp:        secure_utils.NewSmartDLP(client),
		firewall:   secure_utils.NewDBFirewall(client),
		summarizer: secure_utils.NewContentSummarizer(client),
		client:     client,
	}

	// 4. 注册路由
	http.HandleFunc("/health", func(w http.ResponseWriter, r *http.Request) {
		sendJSON(w, 200, map[string]string{"status": "ok"})
	})

	http.HandleFunc("/api/v1/dlp/mask", srv.handleDLP)
	http.HandleFunc("/api/v1/firewall/detect", srv.handleFirewall)
	http.HandleFunc("/api/v1/summarizer/generate", srv.handleSummarizer)
	http.HandleFunc("/api/v1/balance", srv.handleBalance)

	port := ":58080"
	fmt.Printf("API Server 启动在 http://localhost%s\n", port)
	if err := http.ListenAndServe(port, nil); err != nil {
		log.Fatal("服务器启动失败: ", err)
	}
}

// --- Handler Implementations ---

func (s *Server) handleDLP(w http.ResponseWriter, r *http.Request) {
	if r.Method != http.MethodPost {
		sendError(w, 405, "Method Not Allowed")
		return
	}
	var req struct {
		Text string `json:"text"`
	}
	if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
		sendError(w, 400, "Invalid JSON")
		return
	}
	masked, err := s.dlp.MaskSensitiveData(req.Text)
	if err != nil {
		sendError(w, 500, err.Error())
		return
	}
	sendJSON(w, 200, map[string]string{"masked_text": masked})
}

func (s *Server) handleFirewall(w http.ResponseWriter, r *http.Request) {
	if r.Method != http.MethodPost {
		sendError(w, 405, "Method Not Allowed")
		return
	}
	var req struct {
		SQL string `json:"sql"`
	}
	if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
		sendError(w, 400, "Invalid JSON")
		return
	}
	isSafe, reason, err := s.firewall.DetectIntrusion(req.SQL)
	if err != nil {
		sendError(w, 500, err.Error())
		return
	}
	sendJSON(w, 200, map[string]interface{}{
		"is_safe": isSafe,
		"reason":  reason,
	})
}

func (s *Server) handleSummarizer(w http.ResponseWriter, r *http.Request) {
	if r.Method != http.MethodPost {
		sendError(w, 405, "Method Not Allowed")
		return
	}
	var req struct {
		Content string `json:"content"`
	}
	if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
		sendError(w, 400, "Invalid JSON")
		return
	}
	res, err := s.summarizer.GenerateSummary(req.Content)
	if err != nil {
		sendError(w, 500, err.Error())
		return
	}
	sendJSON(w, 200, res) // res is already struct with json tags
}

func (s *Server) handleBalance(w http.ResponseWriter, r *http.Request) {
	if r.Method != http.MethodGet {
		sendError(w, 405, "Method Not Allowed")
		return
	}
	balance, err := s.client.GetBalance()
	if err != nil {
		sendError(w, 500, err.Error())
		return
	}
	sendJSON(w, 200, balance)
}
