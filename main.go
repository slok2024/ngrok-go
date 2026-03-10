package main

import (
	"context"
	"fmt"
	"net/http"
	"net/http/httputil"
	"net/url"
	"os"
	"golang.ngrok.com/ngrok"
	"golang.ngrok.com/ngrok/config"
)

func main() {
	// 默认端口修改为 80
	localPort := "80"
	if len(os.Args) > 1 {
		localPort = os.Args[1]
	}

	ctx := context.Background()
	// 注意：这里建议将 Authtoken 保持在代码中或由 GUI 传入
	tun, err := ngrok.Listen(ctx,
		config.HTTPEndpoint(),
		ngrok.WithAuthtoken("3AkuDCywaOxLKcPhEpQ9szDVg6z_TsTXvVSPEBWDBorABxbt"),
	)
	if err != nil {
		// 输出 Error: 开头的信息，方便 Python 识别错误
		fmt.Fprintf(os.Stderr, "Error: %v\n", err)
		os.Exit(1)
	}

	// 打印 URL 给 Python GUI 读取
	fmt.Printf("STATUS:CONNECTED\n")
	fmt.Printf("URL:%s\n", tun.URL())
	fmt.Printf("TARGET:127.0.0.1:%s\n", localPort)

	target, _ := url.Parse("http://127.0.0.1:" + localPort)
	proxy := httputil.NewSingleHostReverseProxy(target)

	// 启动反向代理服务
	if err := http.Serve(tun, proxy); err != nil {
		fmt.Fprintf(os.Stderr, "Serve Error: %v\n", err)
	}
}