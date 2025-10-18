# --- Build stage ---
FROM golang:1.22-alpine AS builder
WORKDIR /app

# Install build dependencies
RUN apk add --no-cache git

# Copy go files and build
COPY go.mod go.sum ./
RUN go mod download

COPY . .
RUN go build -o whatsapp-bridge main.go

# --- Run stage ---
FROM alpine:3.20
WORKDIR /app

# Copy built binary
COPY --from=builder /app/whatsapp-bridge /app/whatsapp-bridge

# Create directory for WhatsApp session
RUN mkdir -p /app/store
VOLUME ["/app/store"]

# Expose port 
EXPOSE 3000

# Start bridge
CMD ["./whatsapp-bridge"]

