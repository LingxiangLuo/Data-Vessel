<template>
  <div class="admin-page">
    <div class="page-header">
      <h2>通知配置</h2>
    </div>

    <!-- SMTP 服务器配置 -->
    <a-card :bordered="false" title="SMTP 邮件服务器" style="margin-bottom: 16px">
      <a-form :model="smtpForm" layout="vertical" style="max-width: 560px">
        <a-row :gutter="16">
          <a-col :span="16">
            <a-form-item label="SMTP 服务器">
              <a-input v-model="smtpForm.host" placeholder="smtp.163.com" />
            </a-form-item>
          </a-col>
          <a-col :span="8">
            <a-form-item label="端口">
              <a-input-number v-model="smtpForm.port" :min="1" :max="65535" style="width: 100%" />
            </a-form-item>
          </a-col>
        </a-row>
        <a-form-item label="发件人账号">
          <a-input v-model="smtpForm.user" placeholder="your@email.com" />
        </a-form-item>
        <a-form-item label="授权码 / 密码">
          <a-input-password v-model="smtpForm.password" placeholder="SMTP 授权码" />
        </a-form-item>
        <a-form-item label="发件人名称">
          <a-input v-model="smtpForm.sender_name" placeholder="数据中台" />
        </a-form-item>
        <a-form-item label="加密方式">
          <a-radio-group v-model="smtpForm.use_ssl">
            <a-radio :value="true">SSL (推荐)</a-radio>
            <a-radio :value="false">STARTTLS</a-radio>
          </a-radio-group>
        </a-form-item>
        <a-space>
          <a-button type="primary" @click="saveSmtp" :loading="smtpSaving">保存 SMTP 配置</a-button>
          <a-button @click="testSmtp" :loading="smtpTesting">发送测试邮件</a-button>
        </a-space>
      </a-form>
      <a-alert type="info" style="margin-top: 12px">
        邮件服务器配置为全局共用。创建 email 类型通知渠道时，只需指定收件人地址。
      </a-alert>
    </a-card>

    <!-- 通知渠道管理 -->
    <a-card :bordered="false" title="通知渠道">
      <template #extra>
        <a-button type="primary" size="small" @click="openCreate">
          <template #icon><icon-plus /></template>
          新建渠道
        </a-button>
      </template>

      <a-table :data="channels" :loading="loading" :bordered="false" :pagination="false" stripe>
        <template #columns>
          <a-table-column title="渠道名称" data-index="name" :width="200" />
          <a-table-column title="类型" :width="140">
            <template #cell="{ record }">
              <a-tag :color="typeColor(record.type)" size="small">{{ typeLabel(record.type) }}</a-tag>
            </template>
          </a-table-column>
          <a-table-column title="配置摘要" :width="260">
            <template #cell="{ record }">
              <span class="config-summary">{{ configSummary(record) }}</span>
            </template>
          </a-table-column>
          <a-table-column title="状态" :width="80">
            <template #cell="{ record }">
              <a-tag :color="record.enabled ? 'green' : 'red'" size="small">
                {{ record.enabled ? '启用' : '停用' }}
              </a-tag>
            </template>
          </a-table-column>
          <a-table-column title="操作" :width="200">
            <template #cell="{ record }">
              <a-space :size="4">
                <a-button type="text" size="mini" @click="handleTest(record)">测试</a-button>
                <a-button type="text" size="mini" @click="openEdit(record)">编辑</a-button>
                <a-button type="text" size="mini" status="danger" @click="handleDelete(record)">删除</a-button>
              </a-space>
            </template>
          </a-table-column>
        </template>
        <template #empty>
          <div class="empty-state">
            <p>暂无通知渠道</p>
            <p class="text-muted">点击「新建渠道」创建飞书/钉钉/企微机器人或邮件收件人</p>
          </div>
        </template>
      </a-table>
    </a-card>

    <!-- 新建/编辑渠道弹窗 -->
    <a-modal
      v-model:visible="modalVisible"
      :title="editingId ? '编辑渠道' : '新建渠道'"
      :width="520"
      @ok="handleSave"
      @cancel="resetModal"
      :unmount-on-close="true"
    >
      <a-form :model="chForm" layout="vertical">
        <a-form-item label="渠道名称" required>
          <a-input v-model="chForm.name" placeholder="例如：运维群-飞书机器人" />
        </a-form-item>
        <a-form-item label="渠道类型" required>
          <a-select v-model="chForm.type" @change="onTypeChange">
            <a-option value="feishu_webhook">飞书机器人 Webhook</a-option>
            <a-option value="dingtalk_webhook">钉钉机器人 Webhook</a-option>
            <a-option value="wecom_webhook">企业微信机器人 Webhook</a-option>
            <a-option value="email">邮件</a-option>
          </a-select>
        </a-form-item>
        <a-form-item v-if="chForm.type !== 'email'" label="Webhook URL" required>
          <a-input v-model="chForm.webhook_url" placeholder="https://..." />
        </a-form-item>
        <a-form-item v-if="chForm.type === 'dingtalk_webhook'" label="签名密钥 (选填)">
          <a-input v-model="chForm.secret" placeholder="SEC..." />
        </a-form-item>
        <a-form-item v-if="chForm.type === 'email'" label="收件人邮箱" required>
          <a-textarea
            v-model="chForm.emails"
            placeholder="每行一个邮箱地址&#10;alert@corp.com&#10;admin@corp.com"
            :auto-size="{ minRows: 2, maxRows: 6 }"
          />
          <div class="field-hint">每行一个邮箱地址</div>
        </a-form-item>
        <a-form-item label="启用">
          <a-switch v-model="chForm.enabled" />
        </a-form-item>
      </a-form>
    </a-modal>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, reactive } from 'vue'
import { Message, Modal } from '@arco-design/web-vue'
import { IconPlus } from '@arco-design/web-vue/es/icon'
import {
  adminGetConfig, adminSetConfig, adminTestSmtp,
  adminListChannels, adminCreateChannel, adminUpdateChannel, adminDeleteChannel, adminTestChannel,
} from '../../api'

interface Channel {
  id: number
  name: string
  type: string
  config: any
  enabled: boolean
}

const loading = ref(false)
const channels = ref<Channel[]>([])
const smtpSaving = ref(false)
const smtpTesting = ref(false)
const smtpForm = ref({ host: 'smtp.163.com', port: 465, user: '', password: '', sender_name: '数据中台', use_ssl: true })
const modalVisible = ref(false)
const editingId = ref<number | null>(null)
const chForm = reactive({ name: '', type: 'feishu_webhook', webhook_url: '', secret: '', emails: '', enabled: true })

const typeColor = (t: string) => ({ feishu_webhook: 'blue', dingtalk_webhook: 'cyan', wecom_webhook: 'green', email: 'orange' }[t] || 'gray')
const typeLabel = (t: string) => ({ feishu_webhook: '飞书机器人', dingtalk_webhook: '钉钉机器人', wecom_webhook: '企微机器人', email: '邮件' }[t] || t)
function configSummary(r: Channel) {
  const c = r.config || {}
  if (r.type === 'email') return Array.isArray(c.email) ? c.email.join(', ') : (c.email || '-')
  return c.webhook_url || '-'
}

function onTypeChange() { chForm.webhook_url = ''; chForm.secret = ''; chForm.emails = '' }
function resetModal() { modalVisible.value = false; editingId.value = null }

async function loadSmtp() {
  try { const res: any = await adminGetConfig('smtp_config'); if (res?.value) Object.assign(smtpForm.value, res.value) } catch {}
}
async function saveSmtp() {
  smtpSaving.value = true
  try { await adminSetConfig('smtp_config', { value: { ...smtpForm.value }, description: 'SMTP 邮件配置' }); Message.success('SMTP 配置已保存') }
  finally { smtpSaving.value = false }
}
async function testSmtp() {
  smtpTesting.value = true
  try { await adminTestSmtp(); Message.success('测试邮件已发送') }
  finally { smtpTesting.value = false }
}

async function loadChannels() {
  loading.value = true
  try { const res: any = await adminListChannels(); channels.value = Array.isArray(res) ? res : (res?.items || []) }
  catch { channels.value = [] }
  loading.value = false
}

function openCreate() {
  editingId.value = null
  Object.assign(chForm, { name: '', type: 'feishu_webhook', webhook_url: '', secret: '', emails: '', enabled: true })
  modalVisible.value = true
}
function openEdit(r: Channel) {
  editingId.value = r.id
  const c = r.config || {}
  Object.assign(chForm, {
    name: r.name, type: r.type, enabled: r.enabled,
    webhook_url: c.webhook_url || '', secret: c.secret || '',
    emails: Array.isArray(c.email) ? c.email.join('\n') : (c.email || ''),
  })
  modalVisible.value = true
}

function buildConfig() {
  if (chForm.type === 'email') return { email: chForm.emails.split('\n').map(s => s.trim()).filter(Boolean) }
  const cfg: any = { webhook_url: chForm.webhook_url.trim() }
  if (chForm.type === 'dingtalk_webhook' && chForm.secret.trim()) cfg.secret = chForm.secret.trim()
  return cfg
}

async function handleSave() {
  if (!chForm.name.trim()) { Message.warning('请填写渠道名称'); return }
  if (chForm.type !== 'email' && !chForm.webhook_url.trim()) { Message.warning('请填写 Webhook URL'); return }
  if (chForm.type === 'email' && !chForm.emails.trim()) { Message.warning('请填写收件人邮箱'); return }
  const payload = { name: chForm.name.trim(), type: chForm.type, config: buildConfig(), enabled: chForm.enabled }
  try {
    if (editingId.value) { await adminUpdateChannel(editingId.value, payload); Message.success('已更新') }
    else { await adminCreateChannel(payload); Message.success('已创建') }
    modalVisible.value = false; loadChannels()
  } catch {}
}

async function handleTest(r: Channel) {
  try { await adminTestChannel(r.id); Message.success(`测试消息已发送到「${r.name}」`) }
  catch (e: any) { Message.error(e?.response?.data?.detail || '发送失败') }
}

function handleDelete(r: Channel) {
  Modal.confirm({
    title: '删除渠道',
    content: `确认删除「${r.name}」？删除后引用此渠道的告警规则将失效。`,
    onOk: async () => { try { await adminDeleteChannel(r.id); Message.success('已删除'); loadChannels() } catch {} },
  })
}

onMounted(() => { loadSmtp(); loadChannels() })
</script>

<style scoped>
.admin-page { padding: 0; }
.page-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 16px; }
.page-header h2 { margin: 0; font-size: 18px; font-weight: 600; color: #1D2129; }
.config-summary { font-size: 12px; color: #86909C; word-break: break-all; }
.field-hint { margin-top: 4px; font-size: 12px; color: #86909C; }
.empty-state { padding: 40px 0; text-align: center; }
.text-muted { color: #86909C; }
</style>
