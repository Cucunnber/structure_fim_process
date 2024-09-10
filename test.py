import parser

from function_process import *



# 示例用法
function_string = """ULONG slsp_cli_ParseIngressLsp(IN VOID *pCfgMsg)
{
    IF_SELECT_S stSelect;
    CHAR   szIfName[IF_MAX_NAME_LEN+1];

    /* 获取配置消息中的MOR信息 */
    memset(&stSlsp, 0, sizeof(SLSP_CFG_S));
    stSlsp.uiInLabel = LSM_INVALID_LABEL;
    pDestAddr = &(stSlsp.stDestAddr.s_addr);

    /* 判断是否是二阶段生效模式do操作 */
    ulView = getCurrentViewMode();

    /* 模拟两行注释,
       这是第二行 */
    uiEmbedSrcAddr = TUNN4_6O4_GETEMBEDIPV4ADDR(&(pstIP6->stIp6Src),
                                                 pstCoreData->ucIPv6PrefixLen,
                                                 INET_ADDR_IP4ADDRUINT(&(pstCoreData->stSrcAddr)),
                                                 pstCoreData->ucIPv4PrefixLen,
                                                 pstCoreData->ucIPv4SuffixLen);

    return SLSP_SetStaticLsp(bUndoFlag, &stSlsp);
}"""





ret = extract_comment_block(function_string)

ss = ret[0] + ret[1] + ret[2]

print(ret[1])