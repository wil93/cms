{{- define "cms.annot" }}
{{- if . }}
{{- toYaml . }}
{{- end }}
{{- end }}

{{- define "cms.deployment" }}
{{ $service := printf "%s-%s" .Release.Name .service }}
{{ $persistance := default (dict) .persistance }}
apiVersion: apps/v1
kind: {{ default "Deployment" .kind }}
metadata:
  name: {{ $service }}
  annotations:
    {{- include "cms.annot" .annotations | nindent 4 }}
  labels:
    app: {{ $service }}
    {{- include "cms.annot" .labels | nindent 4 }}
spec:
  replicas: {{ .replicas }}
  {{- if eq (default "Deployment" .kind) "StatefulSet" }}
  serviceName: {{ $service }}
  {{- end }}
  selector:
    matchLabels:
      app: {{ $service }}
  template:
    metadata:
      annotations:
        {{- include "cms.annot" .podAnnotations | nindent 8 }}
      labels:
        app: {{ $service }}
        {{- include "cms.annot" .podLabels | nindent 8 }}
    spec:
      imagePullSecrets: {{ .pullSecrets }}
      nodeSelector:
        {{- toYaml .nodeSelector | nindent 8 }}
      tolerations:
        {{- toYaml .tolerations | nindent 8 }}
      affinity:
        {{- toYaml .affinity | nindent 8 }}
      containers:
      - name: {{ $service }}
        image: {{ .image }}:{{ default $.Chart.AppVersion .tag }}
        imagePullPolicy: {{ .pullPolicy }}
        resources:
          {{- toYaml .resources | nindent 10 }}
        {{- if .privileged }}
        securityContext:
          privileged: true
        {{- end }}
        env:
        - name: CMS_PROXY_SERVICE_DISABLED
          value: {{ ternary "false" "true" .Values.core.proxy.enabled | quote }}
        - name: CMS_CONTEST_ID
          value: {{ .Values.cms.contestId | quote }}
        {{- if .Values.core.proxy.contestId }}
        - name: CMS_PROXY_SERVICE_CONTEST_ID
          value: {{ .Values.core.proxy.contestId | quote }}
        {{- end }}
        - name: PUID
          value: {{ .Values.cms.uid | quote }}
        - name: PGID
          value: {{ .Values.cms.gid | quote }}
        - name: TZ
          value: {{ .Values.cms.timeZone | quote }}
        - name: CMS_SECRET_KEY_FILE
          value: /config/secretKey/secretKey.txt
        {{- if .Values.db.fromSecret }}
        - name: CMS_DATABASE_FILE
          value: /config/db/db.txt
        {{- end }}
        {{- if .port }}
        ports:
        - containerPort: {{ .port }}
        {{- end }}
        volumeMounts:
        - name: config
          mountPath: /config
        - name: secret-key
          mountPath: /config/secretKey
          readOnly: true
        - name: logs
          mountPath: /config/logs
          {{- if and (not (eq .service "ranking")) $persistance.subPath }}
          subPath: {{ $persistance.subPath }}
          {{- end }}
        {{- if .Values.db.fromSecret }}
        - name: database-url
          mountPath: /config/db
          readOnly: true
        {{- end }}
        {{- if eq .service "ranking" }}
        - name: ranking-data
          mountPath: /config/ranking
          {{- if $persistance.subPath }}
          subPath: {{ $persistance.subPath }}
          {{- end }}
        {{- end }}
        {{- with .additionalVolumeMounts }}
        {{ . | nindent 8 }}
        {{- end }}
        {{- if .port }}
        {{- if not (eq .service "worker") }}
        livenessProbe:
          httpGet:
            path: /
            port: {{ .port }}
          initialDelaySeconds: 3
          periodSeconds: 15
        {{- end }}
        {{- end }}
      volumes:
      - name: config
        configMap:
          name: {{ .Release.Name }}-config
          items:
          - key: cms.conf
            path: cms.conf
          - key: cms.ranking.conf
            path: cms.ranking.conf
      - name: secret-key
        secret:
          secretName: {{ default (printf "%s-secretkey" .Release.Name) .Values.cms.secretKey.secretName }}
          items:
          - key: {{ default "secretKey" .Values.cms.secretKey.secretKey }}
            path: secretKey.txt
      {{- if .Values.db.fromSecret }}
      - name: database-url
        secret:
          secretName: {{ .Values.db.fromSecret.secretName }}
          items:
          - key: {{ .Values.db.fromSecret.secretKey }}
            path: db.txt
      {{- end }}
      - name: logs
        {{- if and (not (eq .service "ranking")) $persistance.enabled }}
        persistentVolumeClaim:
          claimName: {{ $persistance.existingClaim | default (printf "%s-logs" $service) }}
        {{- else }}
        emptyDir: {}
        {{- end }}
      {{- if eq .service "ranking" }}
      - name: ranking-data
        {{- if $persistance.enabled }}
        persistentVolumeClaim:
          claimName: {{ $persistance.existingClaim | default (printf "%s-data" $service) }}
        {{- else }}
        emptyDir: {}
        {{- end }}
      {{- end }}
      {{- with .additionalVolumes }}
      {{ . | nindent 6 }}
      {{- end }}
{{- end }}

{{- define "cms.ingress" }}
{{- if .ingress.enabled }}
{{- if .ingress.traefik }}
apiVersion: traefik.containo.us/v1alpha1
kind: IngressRoute
metadata:
  name: {{ .Release.Name }}-{{ .service }}
  annotations:
    {{- include "cms.annot" .ingress.annotations | nindent 4 }}
  labels:
    app: {{ .Release.Name }}-{{ .service }}
    {{- include "cms.annot" .ingress.labels | nindent 4 }}
spec:
  routes:
    - match: Host(`{{ .ingress.host }}`) && PathPrefix(`{{ .ingress.path }}`)
      kind: Rule
      services:
        - name: {{ .Release.Name }}-{{ .service }}
          port: {{ .port }}
      middlewares:
        {{- if .ingress.basicAuth }}
        - name: {{ .Release.Name }}-{{ .service }}-basicauth
        {{- end }}
        - name: {{ .Release.Name }}-{{ .service }}-stipprefix
---
apiVersion: traefik.containo.us/v1alpha1
kind: Middleware
metadata:
  name: {{ .Release.Name }}-{{ .service }}-stipprefix
spec:
  stripPrefix:
    prefixes:
      - {{ .ingress.path }}
{{- if .ingress.basicAuth }}
---
apiVersion: traefik.containo.us/v1alpha1
kind: Middleware
metadata:
  name: {{ .Release.Name }}-{{ .service }}-basicauth
spec:
  basicAuth:
    secret: {{ .Release.Name }}-{{ .service }}-basicauth
---
apiVersion: v1
kind: Secret
metadata:
  name: {{ .Release.Name }}-{{ .service }}-basicauth
stringData:
  users: |
    {{- range .ingress.basicAuth }}
    {{ htpasswd .username .password }}
    {{- end }}
{{- end }}
{{- else -}}
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: {{ .Release.Name }}-{{ .service }}
  annotations:
    {{- include "cms.annot" .ingress.annotations | nindent 4 }}
    {{- if .ingress.basicAuth }}
    nginx.ingress.kubernetes.io/auth-type: basic
    nginx.ingress.kubernetes.io/auth-secret: {{ .Release.Name }}-{{ .service }}-basicauth
    nginx.ingress.kubernetes.io/auth-realm: 'Authentication Required'
    {{- end }}
  labels:
    app: {{ .Release.Name }}-{{ .service }}
    {{- include "cms.annot" .ingress.labels | nindent 4 }}
spec:
  rules:
  - host: {{ .ingress.host }}
    http:
      paths:
      - pathType: {{ .ingress.pathType }}
        path: {{ .ingress.path | quote }}
        backend:
          service:
            name: {{ .Release.Name }}-{{ .service }}
            port:
              number: {{ .port }}
  {{- if .ingress.tls }}
  tls:
  {{- toYaml .ingress.tls | nindent 4 }}
  {{- end }}
{{- if .ingress.basicAuth }}
---
apiVersion: v1
kind: Secret
metadata:
  name: {{ .Release.Name }}-{{ .service }}-basicauth
stringData:
  auth: |
    {{- range .ingress.basicAuth }}
    {{ htpasswd .username .password }}
    {{- end }}
{{- end }}
{{- end }}
{{- end }}
{{- end }}
